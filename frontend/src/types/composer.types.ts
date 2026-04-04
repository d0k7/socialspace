// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\types\composer.types.ts

/**
 * Post Composer Type Definitions
 * 
 * FAANG++++ Standards:
 * - Strict TypeScript types
 * - Comprehensive interfaces
 * - Platform-specific constants
 * - Form validation types
 */

// ============================================================================
// PLATFORM CONFIGURATION
// ============================================================================

export const PLATFORM_LIMITS = {
  twitter: {
    maxChars: 280,
    maxImages: 4,
    maxVideos: 1,
    videoMaxSize: 512 * 1024 * 1024, // 512MB
    imageMaxSize: 5 * 1024 * 1024, // 5MB
  },
  linkedin: {
    maxChars: 3000,
    maxImages: 9,
    maxVideos: 1,
    videoMaxSize: 200 * 1024 * 1024, // 200MB
    imageMaxSize: 10 * 1024 * 1024, // 10MB
  },
  instagram: {
    maxChars: 2200,
    maxImages: 10,
    maxVideos: 1,
    videoMaxSize: 100 * 1024 * 1024, // 100MB
    imageMaxSize: 8 * 1024 * 1024, // 8MB
  },
  facebook: {
    maxChars: 63206,
    maxImages: 10,
    maxVideos: 1,
    videoMaxSize: 1024 * 1024 * 1024, // 1GB
    imageMaxSize: 10 * 1024 * 1024, // 10MB
  },
  telegram: {
    maxChars: 4096,
    maxImages: 10,
    maxVideos: 1,
    videoMaxSize: 2048 * 1024 * 1024, // 2GB
    imageMaxSize: 10 * 1024 * 1024, // 10MB
  },
  discord: {
    maxChars: 2000,
    maxImages: 10,
    maxVideos: 1,
    videoMaxSize: 8 * 1024 * 1024, // 8MB (free tier)
    imageMaxSize: 8 * 1024 * 1024, // 8MB
  },
  reddit: {
    maxChars: 40000,
    maxImages: 20,
    maxVideos: 1,
    videoMaxSize: 1024 * 1024 * 1024, // 1GB
    imageMaxSize: 20 * 1024 * 1024, // 20MB
  },
  youtube: {
    maxChars: 5000, // Description
    maxImages: 1, // Thumbnail
    maxVideos: 1,
    videoMaxSize: 256 * 1024 * 1024 * 1024, // 256GB (but we'll limit to 10GB)
    imageMaxSize: 2 * 1024 * 1024, // 2MB
  },
  whatsapp: {
    maxChars: 65536,
    maxImages: 10,
    maxVideos: 1,
    videoMaxSize: 16 * 1024 * 1024, // 16MB
    imageMaxSize: 16 * 1024 * 1024, // 16MB
  },
  tiktok: {
    maxChars: 150, // Caption
    maxImages: 0,
    maxVideos: 1,
    videoMaxSize: 287 * 1024 * 1024, // 287MB
    imageMaxSize: 0,
  },
  snapchat: {
    maxChars: 250,
    maxImages: 1,
    maxVideos: 1,
    videoMaxSize: 32 * 1024 * 1024, // 32MB
    imageMaxSize: 5 * 1024 * 1024, // 5MB
  },
  pinterest: {
    maxChars: 500,
    maxImages: 1,
    maxVideos: 1,
    videoMaxSize: 100 * 1024 * 1024, // 100MB
    imageMaxSize: 20 * 1024 * 1024, // 20MB
  },
} as const;

export type PlatformType = keyof typeof PLATFORM_LIMITS;

export const PLATFORMS: PlatformType[] = [
  'twitter',
  'linkedin',
  'instagram',
  'facebook',
  'telegram',
  'discord',
  'reddit',
  'youtube',
  'whatsapp',
  'tiktok',
  'snapchat',
  'pinterest',
];

// Platform display names
export const PLATFORM_NAMES: Record<PlatformType, string> = {
  twitter: 'Twitter',
  linkedin: 'LinkedIn',
  instagram: 'Instagram',
  facebook: 'Facebook',
  telegram: 'Telegram',
  discord: 'Discord',
  reddit: 'Reddit',
  youtube: 'YouTube',
  whatsapp: 'WhatsApp',
  tiktok: 'TikTok',
  snapchat: 'Snapchat',
  pinterest: 'Pinterest',
};

// Platform colors (for UI)
export const PLATFORM_COLORS: Record<PlatformType, string> = {
  twitter: '#1DA1F2',
  linkedin: '#0A66C2',
  instagram: '#E4405F',
  facebook: '#1877F2',
  telegram: '#0088cc',
  discord: '#5865F2',
  reddit: '#FF4500',
  youtube: '#FF0000',
  whatsapp: '#25D366',
  tiktok: '#000000',
  snapchat: '#FFFC00',
  pinterest: '#E60023',
};

// ============================================================================
// MEDIA TYPES
// ============================================================================

export interface MediaFile {
  id: string;
  file: File;
  type: 'image' | 'video';
  url: string; // Preview URL (blob)
  uploadProgress?: number; // 0-100
  uploadedUrl?: string; // Server URL after upload
  error?: string;
}

export const ALLOWED_IMAGE_TYPES = [
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
];

export const ALLOWED_VIDEO_TYPES = [
  'video/mp4',
  'video/quicktime',
  'video/x-msvideo',
];

// ============================================================================
// POST COMPOSER STATE
// ============================================================================

export interface PostDraft {
  id: string;
  content: string;
  platforms: PlatformType[];
  media: MediaFile[];
  scheduledFor?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface ComposerFormData {
  content: string;
  platforms: PlatformType[];
  media: MediaFile[];
  scheduleType: 'now' | 'scheduled';
  scheduledFor?: Date;
  timezone?: string;
}

// ============================================================================
// VALIDATION TYPES
// ============================================================================

export interface ValidationError {
  field: string;
  message: string;
  platform?: PlatformType;
}

export interface ContentValidation {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
}

export interface PlatformValidation {
  platform: PlatformType;
  isValid: boolean;
  characterCount: number;
  characterLimit: number;
  exceedsLimit: boolean;
  imageCount: number;
  imageLimit: number;
  exceedsImageLimit: boolean;
  videoCount: number;
  videoLimit: number;
  exceedsVideoLimit: boolean;
  errors: string[];
}

// ============================================================================
// API TYPES
// ============================================================================

export interface CreatePostRequest {
  content: string;
  platforms: PlatformType[];
  media_urls?: string[];
  scheduled_for?: string; // ISO 8601
  timezone?: string;
}

export interface CreatePostResponse {
  post_id: string;
  status: 'scheduled' | 'published' | 'draft';
  scheduled_for?: string;
  created_at: string;
}

export interface UploadMediaRequest {
  file: File;
  type: 'image' | 'video';
}

export interface UploadMediaResponse {
  media_id: string;
  url: string;
  cdn_url: string;
  type: 'image' | 'video';
  size: number;
  uploaded_at: string;
}

// ============================================================================
// PREVIEW TYPES
// ============================================================================

export interface PlatformPreview {
  platform: PlatformType;
  content: string;
  media: MediaFile[];
  characterCount: number;
  truncated: boolean; // If content exceeds limit
}

// ============================================================================
// CHARACTER COUNTER TYPES
// ============================================================================

export interface CharacterCountStatus {
  count: number;
  limit: number;
  percentage: number; // 0-100
  status: 'safe' | 'warning' | 'danger'; // <80%, 80-95%, >95%
}

// ============================================================================
// SCHEDULE PICKER TYPES
// ============================================================================

export interface ScheduleOption {
  type: 'now' | 'scheduled';
  date?: Date;
  timezone?: string;
}

export const TIMEZONES = [
  { value: 'UTC', label: 'UTC' },
  { value: 'America/New_York', label: 'Eastern Time (US)' },
  { value: 'America/Chicago', label: 'Central Time (US)' },
  { value: 'America/Denver', label: 'Mountain Time (US)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (US)' },
  { value: 'Europe/London', label: 'London' },
  { value: 'Europe/Paris', label: 'Paris' },
  { value: 'Asia/Tokyo', label: 'Tokyo' },
  { value: 'Asia/Shanghai', label: 'Shanghai' },
  { value: 'Asia/Kolkata', label: 'India (IST)' },
  { value: 'Australia/Sydney', label: 'Sydney' },
] as const;

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Get character limit for a platform
 */
export const getCharacterLimit = (platform: PlatformType): number => {
  return PLATFORM_LIMITS[platform].maxChars;
};

/**
 * Get minimum character limit across selected platforms
 */
export const getMinCharacterLimit = (platforms: PlatformType[]): number => {
  if (platforms.length === 0) return Infinity;
  return Math.min(...platforms.map(p => getCharacterLimit(p)));
};

/**
 * Check if content exceeds limit for any platform
 */
export const exceedsAnyLimit = (
  content: string,
  platforms: PlatformType[]
): boolean => {
  return platforms.some(
    platform => content.length > getCharacterLimit(platform)
  );
};

/**
 * Format file size for display
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
};

/**
 * Validate file type
 */
export const isValidFileType = (
  file: File,
  type: 'image' | 'video'
): boolean => {
  if (type === 'image') {
    return ALLOWED_IMAGE_TYPES.includes(file.type);
  }
  return ALLOWED_VIDEO_TYPES.includes(file.type);
};

/**
 * Validate file size for platform
 */
export const isValidFileSize = (
  file: File,
  platform: PlatformType,
  type: 'image' | 'video'
): boolean => {
  const limits = PLATFORM_LIMITS[platform];
  const maxSize = type === 'image' ? limits.imageMaxSize : limits.videoMaxSize;
  return file.size <= maxSize;
};

/**
 * Get character count status
 */
export const getCharacterCountStatus = (
  count: number,
  limit: number
): CharacterCountStatus => {
  const percentage = (count / limit) * 100;
  
  let status: 'safe' | 'warning' | 'danger';
  if (percentage < 80) {
    status = 'safe';
  } else if (percentage < 95) {
    status = 'warning';
  } else {
    status = 'danger';
  }
  
  return {
    count,
    limit,
    percentage,
    status,
  };
};

/**
 * Generate unique ID
 */
export const generateId = (): string => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Truncate text to limit
 */
export const truncateText = (text: string, limit: number): string => {
  if (text.length <= limit) return text;
  return text.substring(0, limit - 3) + '...';
};