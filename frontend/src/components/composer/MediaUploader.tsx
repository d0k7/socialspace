// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\components\composer\MediaUploader.tsx

/**
 * MediaUploader Component - Drag & Drop File Upload
 * 
 * FAANG++++ Standards:
 * - Drag and drop interface
 * - File type and size validation
 * - Image/video preview with thumbnails
 * - Upload progress indicator
 * - Multiple file support
 * - Platform-specific limits
 * - Error handling with user-friendly messages
 * - Accessibility compliant
 * 
 * Features:
 * - Drag & drop or click to upload
 * - Real-time preview generation
 * - File removal
 * - Automatic validation against platform limits
 * - Progress bars for uploads
 * - Responsive grid layout
 */

import React, { useState, useRef, useCallback } from 'react';
import {
  Upload,
  X,
  Image as ImageIcon,
  Video,
  AlertCircle,
  Loader2,
  CheckCircle2,
  File,
} from 'lucide-react';
import {
  MediaFile,
  PlatformType,
  PLATFORM_LIMITS,
  ALLOWED_IMAGE_TYPES,
  ALLOWED_VIDEO_TYPES,
  formatFileSize,
  isValidFileType,
  generateId,
} from '../../types/composer.types';

// ============================================================================
// INTERFACES
// ============================================================================

interface MediaUploaderProps {
  media: MediaFile[];
  onChange: (media: MediaFile[]) => void;
  selectedPlatforms: PlatformType[];
  maxFiles?: number;
  disabled?: boolean;
}

interface FileValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

// ============================================================================
// COMPONENT
// ============================================================================

export const MediaUploader: React.FC<MediaUploaderProps> = ({
  media,
  onChange,
  selectedPlatforms,
  maxFiles = 10,
  disabled = false,
}) => {
  // ============================================================================
  // STATE
  // ============================================================================

  const [isDragging, setIsDragging] = useState(false);
  const [uploadErrors, setUploadErrors] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragCounterRef = useRef(0);

  // ============================================================================
  // FILE VALIDATION
  // ============================================================================

  const validateFile = useCallback(
    (file: File): FileValidationResult => {
      const errors: string[] = [];
      const warnings: string[] = [];

      // Determine file type
      const isImage = ALLOWED_IMAGE_TYPES.includes(file.type);
      const isVideo = ALLOWED_VIDEO_TYPES.includes(file.type);
      const fileType: 'image' | 'video' | null = isImage
        ? 'image'
        : isVideo
        ? 'video'
        : null;

      // Check file type
      if (!fileType) {
        errors.push(
          `${file.name}: Unsupported file type. Only images (JPEG, PNG, GIF, WebP) and videos (MP4, MOV, AVI) are allowed.`
        );
        return { isValid: false, errors, warnings };
      }

      // Check against platform limits
      if (selectedPlatforms.length > 0) {
        for (const platform of selectedPlatforms) {
          const limits = PLATFORM_LIMITS[platform];

          // Check file size
          const maxSize =
            fileType === 'image' ? limits.imageMaxSize : limits.videoMaxSize;

          if (file.size > maxSize) {
            errors.push(
              `${file.name}: Too large for ${platform}. Maximum size: ${formatFileSize(maxSize)}`
            );
          }

          // Check file count limits
          const currentCount = media.filter(m => m.type === fileType).length;
          const maxCount =
            fileType === 'image' ? limits.maxImages : limits.maxVideos;

          if (currentCount >= maxCount) {
            warnings.push(
              `${platform} allows maximum ${maxCount} ${fileType}${maxCount !== 1 ? 's' : ''}`
            );
          }
        }
      }

      // Check total file limit
      if (media.length >= maxFiles) {
        errors.push(`Maximum ${maxFiles} files allowed`);
      }

      return {
        isValid: errors.length === 0,
        errors,
        warnings,
      };
    },
    [media, selectedPlatforms, maxFiles]
  );

  // ============================================================================
  // FILE HANDLING
  // ============================================================================

  const handleFiles = useCallback(
    async (files: FileList | File[]) => {
      const fileArray = Array.from(files);
      const newMedia: MediaFile[] = [];
      const errors: string[] = [];

      for (const file of fileArray) {
        // Validate file
        const validation = validateFile(file);

        if (!validation.isValid) {
          errors.push(...validation.errors);
          continue;
        }

        // Add warnings (non-blocking)
        if (validation.warnings.length > 0) {
          console.warn('File warnings:', validation.warnings);
        }

        // Determine file type
        const isImage = ALLOWED_IMAGE_TYPES.includes(file.type);
        const type: 'image' | 'video' = isImage ? 'image' : 'video';

        // Create preview URL
        const url = URL.createObjectURL(file);

        // Create media object
        const mediaFile: MediaFile = {
          id: generateId(),
          file,
          type,
          url,
          uploadProgress: 0,
        };

        newMedia.push(mediaFile);
      }

      // Update state
      if (newMedia.length > 0) {
        onChange([...media, ...newMedia]);

        // Simulate upload (replace with actual API call)
        newMedia.forEach(mediaFile => {
          simulateUpload(mediaFile);
        });
      }

      // Set errors
      if (errors.length > 0) {
        setUploadErrors(errors);

        // Clear errors after 5 seconds
        setTimeout(() => {
          setUploadErrors([]);
        }, 5000);
      }
    },
    [media, onChange, validateFile]
  );

  // Simulate file upload (replace with actual API call)
  const simulateUpload = (mediaFile: MediaFile) => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;

      // Update progress
      onChange(
        media.map(m =>
          m.id === mediaFile.id
            ? { ...m, uploadProgress: progress }
            : m
        )
      );

      if (progress >= 100) {
        clearInterval(interval);

        // Mark as uploaded (with fake URL)
        onChange(
          media.map(m =>
            m.id === mediaFile.id
              ? {
                  ...m,
                  uploadProgress: 100,
                  uploadedUrl: `https://cdn.socialspace.ai/media/${m.id}`,
                }
              : m
          )
        );
      }
    }, 200);
  };

  // ============================================================================
  // DRAG & DROP HANDLERS
  // ============================================================================

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current++;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current--;
    if (dragCounterRef.current === 0) {
      setIsDragging(false);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      dragCounterRef.current = 0;

      if (disabled) return;

      const files = e.dataTransfer.files;
      if (files && files.length > 0) {
        handleFiles(files);
      }
    },
    [disabled, handleFiles]
  );

  // ============================================================================
  // FILE INPUT HANDLERS
  // ============================================================================

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFiles(e.target.files);
        // Reset input
        e.target.value = '';
      }
    },
    [handleFiles]
  );

  const handleBrowseClick = useCallback(() => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  }, [disabled]);

  // ============================================================================
  // REMOVE FILE
  // ============================================================================

  const removeFile = useCallback(
    (id: string) => {
      const fileToRemove = media.find(m => m.id === id);
      if (fileToRemove) {
        // Revoke object URL to free memory
        URL.revokeObjectURL(fileToRemove.url);
      }
      onChange(media.filter(m => m.id !== id));
    },
    [media, onChange]
  );

  // ============================================================================
  // COMPUTED VALUES
  // ============================================================================

  const imageCount = media.filter(m => m.type === 'image').length;
  const videoCount = media.filter(m => m.type === 'video').length;

  // Get strictest limits from selected platforms
  const strictestLimits = selectedPlatforms.reduce(
    (acc, platform) => {
      const limits = PLATFORM_LIMITS[platform];
      return {
        maxImages: Math.min(acc.maxImages, limits.maxImages),
        maxVideos: Math.min(acc.maxVideos, limits.maxVideos),
      };
    },
    { maxImages: Infinity, maxVideos: Infinity }
  );

  const hasReachedImageLimit =
    strictestLimits.maxImages !== Infinity &&
    imageCount >= strictestLimits.maxImages;
  const hasReachedVideoLimit =
    strictestLimits.maxVideos !== Infinity &&
    videoCount >= strictestLimits.maxVideos;

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="w-full">
      {/* Upload Area */}
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center transition-colors
          ${isDragging
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleBrowseClick}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="Upload media files"
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleBrowseClick();
          }
        }}
      >
        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          accept={[...ALLOWED_IMAGE_TYPES, ...ALLOWED_VIDEO_TYPES].join(',')}
          multiple
          onChange={handleFileInputChange}
          disabled={disabled}
          className="hidden"
          aria-hidden="true"
        />

        {/* Upload Icon */}
        <div className="flex flex-col items-center gap-3">
          <div className="p-4 rounded-full bg-gray-100 dark:bg-gray-700">
            <Upload className="w-8 h-8 text-gray-600 dark:text-gray-400" />
          </div>

          <div>
            <p className="text-lg font-medium text-gray-900 dark:text-gray-100">
              {isDragging ? 'Drop files here' : 'Drag & drop files here'}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              or click to browse
            </p>
          </div>

          <div className="text-xs text-gray-500 dark:text-gray-500">
            <p>Supported: JPEG, PNG, GIF, WebP, MP4, MOV, AVI</p>
            {selectedPlatforms.length > 0 && (
              <p className="mt-1">
                Limits: {strictestLimits.maxImages !== Infinity ? `${strictestLimits.maxImages} images` : ''}{' '}
                {strictestLimits.maxVideos !== Infinity ? `${strictestLimits.maxVideos} video` : ''}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Upload Errors */}
      {uploadErrors.length > 0 && (
        <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="text-sm font-medium text-red-900 dark:text-red-100">
                Upload errors:
              </div>
              <ul className="text-xs text-red-700 dark:text-red-300 mt-1 list-disc list-inside">
                {uploadErrors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Media Preview Grid */}
      {media.length > 0 && (
        <div className="mt-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Uploaded Media ({media.length})
            </h4>
            {selectedPlatforms.length > 0 && (
              <div className="text-xs text-gray-600 dark:text-gray-400">
                {hasReachedImageLimit && (
                  <span className="text-orange-600 dark:text-orange-400">
                    Image limit reached
                  </span>
                )}
                {hasReachedVideoLimit && (
                  <span className="text-orange-600 dark:text-orange-400 ml-2">
                    Video limit reached
                  </span>
                )}
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {media.map(mediaFile => (
              <MediaPreviewCard
                key={mediaFile.id}
                media={mediaFile}
                onRemove={() => removeFile(mediaFile.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Info Banner */}
      {media.length === 0 && (
        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <div className="flex items-start gap-2">
            <ImageIcon className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-900 dark:text-blue-100">
              <p className="font-medium">Enhance your post with media</p>
              <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                Posts with images get 2.3x more engagement on average
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// MEDIA PREVIEW CARD COMPONENT
// ============================================================================

interface MediaPreviewCardProps {
  media: MediaFile;
  onRemove: () => void;
}

const MediaPreviewCard: React.FC<MediaPreviewCardProps> = ({
  media,
  onRemove,
}) => {
  const isUploading = (media.uploadProgress ?? 0) < 100;
  const isImage = media.type === 'image';

  return (
    <div className="relative group rounded-lg overflow-hidden border border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-800">
      {/* Preview */}
      <div className="aspect-square relative">
        {isImage ? (
          <img
            src={media.url}
            alt="Preview"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center bg-gray-200 dark:bg-gray-700">
            <Video className="w-12 h-12 text-gray-600 dark:text-gray-400" />
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
              Video
            </p>
          </div>
        )}

        {/* Upload Progress Overlay */}
        {isUploading && (
          <div className="absolute inset-0 bg-black/50 flex flex-col items-center justify-center">
            <Loader2 className="w-8 h-8 text-white animate-spin" />
            <div className="mt-2 text-white text-sm font-medium">
              {media.uploadProgress}%
            </div>
            {/* Progress Bar */}
            <div className="mt-2 w-3/4 h-1 bg-gray-300 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 transition-all duration-300"
                style={{ width: `${media.uploadProgress}%` }}
              />
            </div>
          </div>
        )}

        {/* Success Checkmark */}
        {!isUploading && (
          <div className="absolute top-2 right-2 p-1 bg-green-500 rounded-full">
            <CheckCircle2 className="w-4 h-4 text-white" />
          </div>
        )}

        {/* Remove Button */}
        <button
          type="button"
          onClick={onRemove}
          className="absolute top-2 left-2 p-1 bg-red-500 hover:bg-red-600 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
          aria-label="Remove file"
        >
          <X className="w-4 h-4 text-white" />
        </button>
      </div>

      {/* File Info */}
      <div className="p-2 bg-white dark:bg-gray-800 border-t border-gray-300 dark:border-gray-600">
        <div className="flex items-center gap-2">
          {isImage ? (
            <ImageIcon className="w-4 h-4 text-gray-600 dark:text-gray-400 flex-shrink-0" />
          ) : (
            <Video className="w-4 h-4 text-gray-600 dark:text-gray-400 flex-shrink-0" />
          )}
          <div className="flex-1 min-w-0">
            <p className="text-xs text-gray-900 dark:text-gray-100 truncate">
              {media.file.name}
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400">
              {formatFileSize(media.file.size)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// EXPORT
// ============================================================================

export default MediaUploader;