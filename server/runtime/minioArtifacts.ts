import * as Minio from "minio";

const MINIO_ENDPOINT = process.env.MINIO_ENDPOINT || "";
const MINIO_PORT = parseInt(process.env.MINIO_PORT || "9000", 10);
const MINIO_ACCESS_KEY = process.env.MINIO_ACCESS_KEY || "";
const MINIO_SECRET_KEY = process.env.MINIO_SECRET_KEY || "";
const MINIO_BUCKET = process.env.MINIO_ARTIFACT_BUCKET || "bloom-artifacts";
const MINIO_USE_SSL = process.env.MINIO_USE_SSL === "true";

let client: Minio.Client | null = null;
let bucketEnsured = false;

export function isMinioConfigured(): boolean {
  return !!(MINIO_ENDPOINT && MINIO_ACCESS_KEY && MINIO_SECRET_KEY);
}

function getClient(): Minio.Client {
  if (!client) {
    client = new Minio.Client({
      endPoint: MINIO_ENDPOINT,
      port: MINIO_PORT,
      useSSL: MINIO_USE_SSL,
      accessKey: MINIO_ACCESS_KEY,
      secretKey: MINIO_SECRET_KEY,
    });
  }
  return client;
}

async function ensureBucket(): Promise<void> {
  if (bucketEnsured) return;
  const mc = getClient();
  const exists = await mc.bucketExists(MINIO_BUCKET);
  if (!exists) {
    await mc.makeBucket(MINIO_BUCKET, "");
    console.log(`[minio] created bucket: ${MINIO_BUCKET}`);
  }
  bucketEnsured = true;
}

export async function uploadArtifactToMinio(
  objectKey: string,
  content: string
): Promise<string> {
  await ensureBucket();
  const mc = getClient();
  const buf = Buffer.from(content, "utf-8");
  await mc.putObject(MINIO_BUCKET, objectKey, buf, buf.length, {
    "Content-Type": "application/json",
  });
  return `minio://${MINIO_BUCKET}/${objectKey}`;
}

export async function getMinioArtifactUrl(
  objectKey: string,
  expirySeconds = 3600
): Promise<string> {
  const mc = getClient();
  return mc.presignedGetObject(MINIO_BUCKET, objectKey, expirySeconds);
}

export async function downloadArtifactFromMinio(objectKey: string): Promise<string> {
  const mc = getClient();
  const stream = await mc.getObject(MINIO_BUCKET, objectKey);
  const chunks: Buffer[] = [];
  for await (const chunk of stream) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return Buffer.concat(chunks).toString("utf-8");
}
