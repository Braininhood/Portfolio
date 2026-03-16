/**
 * Normalize profile data from the database.
 * - interests can come back as a string (e.g. from CSV import or different client); parse to array.
 * - skill_level must be one of the allowed values or null.
 */

const SKILL_LEVELS = ["beginner", "intermediate", "advanced"] as const;

export function parseInterests(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.filter((v): v is string => typeof v === "string");
  }
  if (typeof value === "string" && value.trim()) {
    try {
      const parsed = JSON.parse(value);
      return Array.isArray(parsed)
        ? parsed.filter((v: unknown): v is string => typeof v === "string")
        : [];
    } catch {
      return [];
    }
  }
  return [];
}

export function parseSkillLevel(value: unknown): string | null {
  if (value == null || value === "") return null;
  const s = String(value).trim().toLowerCase();
  return SKILL_LEVELS.includes(s as (typeof SKILL_LEVELS)[number]) ? s : null;
}

export interface NormalizedProfileRow {
  id: string;
  full_name: string | null;
  avatar_url: string | null;
  goals: string | null;
  interests: string[];
  skill_level: string | null;
  preferred_language: string | null;
  timezone: string | null;
}

export function normalizeProfileFromDb(row: Record<string, unknown> & { id: string }): NormalizedProfileRow {
  return {
    id: row.id,
    full_name: row.full_name != null ? String(row.full_name) : null,
    avatar_url: row.avatar_url != null ? String(row.avatar_url) : null,
    goals: row.goals != null ? String(row.goals) : null,
    interests: parseInterests(row.interests),
    skill_level: parseSkillLevel(row.skill_level),
    preferred_language: row.preferred_language != null ? String(row.preferred_language) : null,
    timezone: row.timezone != null ? String(row.timezone) : null,
  };
}
