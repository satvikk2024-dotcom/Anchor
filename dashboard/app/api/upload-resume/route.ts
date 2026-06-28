import { NextRequest, NextResponse } from "next/server";
import { pool } from "@/lib/db";

const LLM_URL = process.env.LLM_WRAPPER_URL || "http://localhost:8001";

const DECOMPOSE_PROMPT = `You are a resume parser. Extract ALL information from the resume into a structured JSON object. Include every section: education, work experience, projects, skills, achievements, certifications. For each item include all details like dates, tools, metrics, descriptions. Output valid JSON only.`;

async function extractTextFromPDF(buffer: Buffer): Promise<string> {
  const { extractText, getDocumentProxy } = await import("unpdf");
  const doc = await getDocumentProxy(new Uint8Array(buffer));
  const { text } = await extractText(doc, { mergePages: true });
  return text;
}

interface ResumeEntry {
  category: string;
  canonical_text: string;
  facts: Record<string, unknown>;
  tags: string[];
  priority: number;
}

function inferCategory(key: string): string {
  const k = key.toLowerCase();
  if (k.includes("education") || k.includes("degree") || k.includes("school")) return "education";
  if (k.includes("experience") || k.includes("work") || k.includes("intern") || k.includes("job") || k.includes("employment")) return "experience";
  if (k.includes("project")) return "project";
  if (k.includes("skill") || k.includes("language") || k.includes("framework") || k.includes("tool") || k.includes("tech")) return "skill";
  if (k.includes("achievement") || k.includes("award") || k.includes("cert") || k.includes("honor") || k.includes("publication")) return "achievement";
  return "skill";
}

function flattenToEntries(obj: Record<string, unknown>): ResumeEntry[] {
  const entries: ResumeEntry[] = [];
  const skip = new Set(["name", "contact", "email", "phone", "address", "linkedin", "github", "portfolio", "website", "summary", "objective"]);

  for (const [key, value] of Object.entries(obj)) {
    if (skip.has(key.toLowerCase())) continue;
    const category = inferCategory(key);

    if (Array.isArray(value)) {
      if (value.length > 0 && typeof value[0] === "string") {
        entries.push({
          category,
          canonical_text: `${key}: ${value.join(", ")}.`,
          facts: { [key.toLowerCase()]: value },
          tags: value.filter((v): v is string => typeof v === "string").map(v => v.toLowerCase()),
          priority: category === "skill" ? 3 : 4,
        });
      } else {
        for (const item of value) {
          if (typeof item === "object" && item !== null) {
            const desc = Object.values(item as Record<string, unknown>)
              .filter(v => typeof v === "string" || typeof v === "number")
              .join(" — ");
            entries.push({
              category,
              canonical_text: desc || JSON.stringify(item),
              facts: item as Record<string, unknown>,
              tags: extractTags(item as Record<string, unknown>),
              priority: 4,
            });
          } else if (typeof item === "string") {
            entries.push({
              category,
              canonical_text: item,
              facts: {},
              tags: [category],
              priority: 3,
            });
          }
        }
      }
    } else if (typeof value === "object" && value !== null) {
      const desc = Object.entries(value as Record<string, unknown>)
        .filter(([, v]) => typeof v === "string" || typeof v === "number")
        .map(([k, v]) => `${k}: ${v}`)
        .join(", ");
      entries.push({
        category,
        canonical_text: `${key} — ${desc}`,
        facts: value as Record<string, unknown>,
        tags: extractTags(value as Record<string, unknown>),
        priority: category === "education" ? 5 : 4,
      });
    } else if (typeof value === "string" && value.length > 10) {
      entries.push({
        category,
        canonical_text: value,
        facts: {},
        tags: [category],
        priority: 3,
      });
    }
  }

  return entries;
}

function extractTags(obj: Record<string, unknown>): string[] {
  const tags: string[] = [];
  for (const v of Object.values(obj)) {
    if (typeof v === "string" && v.length < 30) tags.push(v.toLowerCase());
    if (Array.isArray(v)) {
      for (const item of v) {
        if (typeof item === "string" && item.length < 30) tags.push(item.toLowerCase());
      }
    }
  }
  return tags.slice(0, 10);
}

async function decomposeWithLLM(resumeText: string): Promise<ResumeEntry[]> {
  const res = await fetch(`${LLM_URL}/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt: `Here is the resume text to parse:\n\n${resumeText}`,
      system_prompt: DECOMPOSE_PROMPT,
      json_mode: true,
      model: "qwen2.5:7b",
    }),
  });

  if (!res.ok) {
    throw new Error(`LLM wrapper returned ${res.status}`);
  }

  const data = await res.json();
  const raw = data.text || data.content || "";

  let parsed: Record<string, unknown>;
  if (typeof raw === "string") {
    const cleaned = raw.replace(/```json\n?/g, "").replace(/```\n?/g, "").trim();
    parsed = JSON.parse(cleaned);
  } else {
    parsed = raw;
  }

  if (parsed.entries && Array.isArray(parsed.entries)) {
    return parsed.entries as ResumeEntry[];
  }

  return flattenToEntries(parsed);
}

const VALID_CATEGORIES = [
  "education",
  "experience",
  "project",
  "skill",
  "achievement",
];

export async function POST(req: NextRequest) {
  const formData = await req.formData();
  const file = formData.get("file") as File | null;
  const mode = (formData.get("mode") as string) || "append";

  if (!file) {
    return NextResponse.json({ error: "No file uploaded" }, { status: 400 });
  }

  const fileName = file.name.toLowerCase();
  if (!fileName.endsWith(".pdf")) {
    return NextResponse.json(
      { error: "Only PDF files are supported" },
      { status: 400 }
    );
  }

  try {
    const buffer = Buffer.from(await file.arrayBuffer());
    const resumeText = await extractTextFromPDF(buffer);

    if (!resumeText.trim()) {
      return NextResponse.json(
        { error: "Could not extract text from PDF — is it a scanned image?" },
        { status: 400 }
      );
    }

    const entries = await decomposeWithLLM(resumeText);

    if (mode === "replace") {
      await pool.query("DELETE FROM material_grounding");
      await pool.query("DELETE FROM master_resume_entry");
    }

    let inserted = 0;
    for (const entry of entries) {
      const category = VALID_CATEGORIES.includes(entry.category as string)
        ? entry.category
        : "skill";
      const canonicalText = entry.canonical_text as string;
      if (!canonicalText) continue;

      const facts = entry.facts ? JSON.stringify(entry.facts) : null;
      const tags = Array.isArray(entry.tags) ? entry.tags : [];
      const priority = typeof entry.priority === "number" ? entry.priority : 3;

      await pool.query(
        `INSERT INTO master_resume_entry (category, canonical_text, facts, tags, priority)
         VALUES ($1, $2, $3, $4, $5)`,
        [category, canonicalText, facts, tags, Math.min(5, Math.max(1, priority))]
      );
      inserted++;
    }

    return NextResponse.json({
      ok: true,
      extracted_chars: resumeText.length,
      entries_created: inserted,
    });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Unknown error during processing";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
