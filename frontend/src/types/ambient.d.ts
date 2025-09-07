declare module 'replicate' {
  const Replicate: any;
  export default Replicate;
}

declare module '@aws-sdk/client-s3' {
  export const S3Client: any;
  export const PutObjectCommand: any;
}

declare module '@aws-sdk/s3-request-presigner' {
  export const getSignedUrl: any;
}

declare module 'uuid' {
  export const v4: any;
}

// Replicate route relative import
declare module '../../../lib/s3' {
  export const s3Storage: any;
}
