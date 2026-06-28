"use server";

import { pool } from "@/lib/db";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

export async function updateProfile(formData: FormData) {
  const name = formData.get("name") as string;
  const email = formData.get("email") as string;
  const phone = formData.get("phone") as string;
  const location = formData.get("location") as string;
  const linkedinUrl = formData.get("linkedin_url") as string;
  const githubUrl = formData.get("github_url") as string;
  const longTermGoals = formData.get("long_term_goals") as string;
  const targetRoleTypes = (formData.get("target_role_types") as string)
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  const existing = await pool.query("SELECT id FROM user_profile LIMIT 1");
  if (existing.rows.length > 0) {
    await pool.query(
      `UPDATE user_profile
       SET name = $1, email = $2, phone = $3, location = $4,
           linkedin_url = $5, github_url = $6,
           long_term_goals = $7, target_role_types = $8, updated_at = now()
       WHERE id = $9`,
      [name || null, email || null, phone || null, location || null,
       linkedinUrl || null, githubUrl || null,
       longTermGoals || null, targetRoleTypes, existing.rows[0].id]
    );
  } else {
    await pool.query(
      `INSERT INTO user_profile (name, email, phone, location, linkedin_url, github_url, long_term_goals, target_role_types)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
      [name || null, email || null, phone || null, location || null,
       linkedinUrl || null, githubUrl || null,
       longTermGoals || null, targetRoleTypes]
    );
  }

  revalidatePath("/setup");
}

export async function createEntry(formData: FormData) {
  const category = formData.get("category") as string;
  const canonicalText = formData.get("canonical_text") as string;
  const tagsRaw = formData.get("tags") as string;
  const priority = formData.get("priority") as string;
  const factsRaw = formData.get("facts") as string;

  const tags = tagsRaw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  let facts = null;
  if (factsRaw && factsRaw.trim()) {
    try {
      facts = JSON.parse(factsRaw);
    } catch {
      facts = null;
    }
  }

  await pool.query(
    `INSERT INTO master_resume_entry (category, canonical_text, facts, tags, priority)
     VALUES ($1, $2, $3, $4, $5)`,
    [
      category,
      canonicalText,
      facts ? JSON.stringify(facts) : null,
      tags,
      priority ? parseInt(priority, 10) : null,
    ]
  );

  redirect("/setup");
}

export async function updateEntry(formData: FormData) {
  const id = formData.get("id") as string;
  const category = formData.get("category") as string;
  const canonicalText = formData.get("canonical_text") as string;
  const tagsRaw = formData.get("tags") as string;
  const priority = formData.get("priority") as string;
  const factsRaw = formData.get("facts") as string;

  const tags = tagsRaw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  let facts = null;
  if (factsRaw && factsRaw.trim()) {
    try {
      facts = JSON.parse(factsRaw);
    } catch {
      facts = null;
    }
  }

  await pool.query(
    `UPDATE master_resume_entry
     SET category = $1, canonical_text = $2, facts = $3, tags = $4, priority = $5
     WHERE id = $6`,
    [
      category,
      canonicalText,
      facts ? JSON.stringify(facts) : null,
      tags,
      priority ? parseInt(priority, 10) : null,
      id,
    ]
  );

  redirect("/setup");
}

export async function deleteEntry(formData: FormData) {
  const id = formData.get("id") as string;

  await pool.query(
    "DELETE FROM material_grounding WHERE master_entry_id = $1",
    [id]
  );
  await pool.query("DELETE FROM master_resume_entry WHERE id = $1", [id]);

  revalidatePath("/setup");
}
