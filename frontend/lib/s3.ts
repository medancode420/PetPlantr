// Minimal stub for type-check.
type S3PutResult = { ok: boolean; key?: string; url?: string; cdnUrl?: string };

export const s3Storage = {
  putObject: async (..._args: any[]): Promise<S3PutResult> => ({ ok: true, key: '', url: '', cdnUrl: '' }),
  getSignedUrl: async (..._args: any[]) => ('') as string,
  uploadGLB: async (..._args: any[]): Promise<S3PutResult> => ({ ok: true, url: '', cdnUrl: '', key: '' }),
  uploadConceptImage: async (..._args: any[]): Promise<S3PutResult> => ({ ok: true, url: '', cdnUrl: '', key: '' }),
};
