/**
 * Upload contents of storage-backup to Supabase Storage.
 *
 * Expected folder structure (bucket name = folder name):
 *   storage-backup/
 *     profile-photos/    → bucket "profile-photos"
 *       <user-id>/file.jpg
 *     mentor-videos/     → bucket "mentor-videos"
 *     avatar-photos/
 *     avatar-voices/
 *
 * Requires: SUPABASE_SERVICE_ROLE_KEY and VITE_SUPABASE_URL in .env
 * Run: node scripts/upload-storage-backup.cjs
 */

const fs = require("fs");
const path = require("path");
const { createClient } = require("@supabase/supabase-js");

const BACKUP_DIR = path.join(__dirname, "..", "storage-backup");

function loadEnv() {
  const envPath = path.join(__dirname, "..", ".env");
  if (!fs.existsSync(envPath)) {
    console.error("No .env file found. Create one with VITE_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.");
    process.exit(1);
  }
  const content = fs.readFileSync(envPath, "utf8");
  const env = {};
  content.split("\n").forEach((line) => {
    const m = line.match(/^\s*([^#=]+)=(.*)$/);
    if (m) env[m[1].trim()] = m[2].trim().replace(/^["']|["']$/g, "");
  });
  return env;
}

function* walkDir(dir, baseDir = dir) {
  if (!fs.existsSync(dir)) return;
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const e of entries) {
    const full = path.join(dir, e.name);
    const rel = path.relative(baseDir, full);
    if (e.isDirectory()) {
      yield* walkDir(full, baseDir);
    } else {
      yield { fullPath: full, relativePath: rel.replace(/\\/g, "/") };
    }
  }
}

function getContentType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const map = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".m4a": "audio/mp4",
    ".mp3": "audio/mpeg",
    ".pdf": "application/pdf",
  };
  return map[ext] || "application/octet-stream";
}

async function main() {
  const env = loadEnv();
  const url = env.VITE_SUPABASE_URL || env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceKey = env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !serviceKey) {
    console.error("Set VITE_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env");
    process.exit(1);
  }

  if (!fs.existsSync(BACKUP_DIR)) {
    console.error("Backup folder not found:", BACKUP_DIR);
    process.exit(1);
  }

  const supabase = createClient(url, serviceKey, { auth: { persistSession: false } });
  const topDirs = fs.readdirSync(BACKUP_DIR, { withFileTypes: true }).filter((d) => d.isDirectory());

  if (topDirs.length === 0) {
    console.log("No subfolders in storage-backup. Expected one folder per bucket (e.g. profile-photos, mentor-videos).");
    process.exit(0);
  }

  let total = 0;
  let ok = 0;
  let err = 0;

  for (const dir of topDirs) {
    const bucket = dir.name;
    const bucketPath = path.join(BACKUP_DIR, bucket);
    console.log("\nBucket:", bucket);

    for (const { fullPath, relativePath } of walkDir(bucketPath, bucketPath)) {
      total++;
      const objectPath = relativePath;
      const fileBuffer = fs.readFileSync(fullPath);

      const { error } = await supabase.storage.from(bucket).upload(objectPath, fileBuffer, {
        upsert: true,
        contentType: getContentType(fullPath),
      });

      if (error) {
        console.error("  FAIL:", objectPath, error.message);
        err++;
      } else {
        console.log("  OK:", objectPath);
        ok++;
      }
    }
  }

  console.log("\nDone. Total:", total, "OK:", ok, "Errors:", err);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
