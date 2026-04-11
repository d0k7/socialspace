// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\components\settings\AIPreferences.tsx

/**
 * AIPreferences Component - AI & Content Customization
 * 
 * FAANG++++ Standards:
 * - AI tone selection
 * - Content style preferences
 * - AI feature toggles
 * - Language preferences
 * - Content length settings
 * - Auto-hashtag generation
 * - Content suggestions
 * - Auto-save
 * - Loading states
 * - Dark mode support
 * 
 * Features:
 * - Tone selection (professional, casual, friendly, creative)
 * - Writing style customization
 * - AI-powered features on/off
 * - Language selection
 * - Content optimization preferences
 * - Auto-improve toggle
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Sparkles,
  MessageSquare,
  Hash,
  Zap,
  Globe,
  Lightbulb,
  Check,
  Loader2,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  Type,
  Image as ImageIcon,
  Wand2,
  Brain,
} from 'lucide-react';
import apiClient from '@/api/client';

// ============================================================================
// INTERFACES
// ============================================================================

interface AIPreferencesProps {
  onSave?: () => void;
}

interface AISettings {
  // Tone & Style
  tone: 'professional' | 'casual' | 'friendly' | 'creative';
  writingStyle: 'concise' | 'detailed' | 'storytelling';
  
  // Language
  language: string;
  
  // AI Features
  autoHashtags: boolean;
  contentSuggestions: boolean;
  grammarCorrection: boolean;
  toneConsistency: boolean;
  emojiSuggestions: boolean;
  imageDescriptions: boolean;
  
  // Content Optimization
  seoOptimization: boolean;
  readabilityEnhancement: boolean;
  engagementOptimization: boolean;
  
  // Preferences
  contentLength: 'short' | 'medium' | 'long';
  autoImprove: boolean;
  creativityLevel: number; // 1-10
}

interface ToneOption {
  value: 'professional' | 'casual' | 'friendly' | 'creative';
  label: string;
  description: string;
  icon: React.ReactNode;
  example: string;
}

interface ToggleProps {
  icon: React.ReactNode;
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  badge?: string;
}

// ============================================================================
// TOGGLE COMPONENT
// ============================================================================

const Toggle: React.FC<ToggleProps> = ({
  icon,
  label,
  description,
  checked,
  onChange,
  disabled = false,
  badge,
}) => (
  <div className="flex items-center justify-between py-4 border-b border-gray-200 dark:border-gray-700 last:border-0">
    <div className="flex items-start gap-3 flex-1">
      <div className="mt-1 text-gray-600 dark:text-gray-400">
        {icon}
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-gray-900 dark:text-gray-100">
            {label}
          </span>
          {badge && (
            <span className="px-2 py-0.5 text-xs font-semibold bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full">
              {badge}
            </span>
          )}
        </div>
        <div className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
          {description}
        </div>
      </div>
    </div>
    
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      disabled={disabled}
      className={`
        relative inline-flex h-6 w-11 items-center rounded-full transition-colors flex-shrink-0
        ${checked ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      <span
        className={`
          inline-block h-4 w-4 transform rounded-full bg-white transition-transform
          ${checked ? 'translate-x-6' : 'translate-x-1'}
        `}
      />
    </button>
  </div>
);

// ============================================================================
// TONE OPTIONS
// ============================================================================

const TONE_OPTIONS: ToneOption[] = [
  {
    value: 'professional',
    label: 'Professional',
    description: 'Formal and business-appropriate',
    icon: <MessageSquare className="w-5 h-5" />,
    example: 'We are pleased to announce our latest product release.',
  },
  {
    value: 'casual',
    label: 'Casual',
    description: 'Relaxed and conversational',
    icon: <MessageSquare className="w-5 h-5" />,
    example: "Hey everyone! Check out what we just launched 🚀",
  },
  {
    value: 'friendly',
    label: 'Friendly',
    description: 'Warm and approachable',
    icon: <MessageSquare className="w-5 h-5" />,
    example: "Hi friends! We're so excited to share this with you!",
  },
  {
    value: 'creative',
    label: 'Creative',
    description: 'Imaginative and expressive',
    icon: <Sparkles className="w-5 h-5" />,
    example: "✨ Imagine a world where... Now it's real! ✨",
  },
];

// ============================================================================
// LANGUAGE OPTIONS
// ============================================================================

const LANGUAGE_OPTIONS = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
  { value: 'de', label: 'German' },
  { value: 'it', label: 'Italian' },
  { value: 'pt', label: 'Portuguese' },
  { value: 'ja', label: 'Japanese' },
  { value: 'ko', label: 'Korean' },
  { value: 'zh', label: 'Chinese' },
  { value: 'hi', label: 'Hindi' },
];

// ============================================================================
// COMPONENT
// ============================================================================

export const AIPreferences: React.FC<AIPreferencesProps> = ({ onSave }) => {
  // ============================================================================
  // STATE
  // ============================================================================

  const [settings, setSettings] = useState<AISettings>({
    tone: 'professional',
    writingStyle: 'concise',
    language: 'en',
    
    autoHashtags: true,
    contentSuggestions: true,
    grammarCorrection: true,
    toneConsistency: true,
    emojiSuggestions: false,
    imageDescriptions: true,
    
    seoOptimization: true,
    readabilityEnhancement: true,
    engagementOptimization: true,
    
    contentLength: 'medium',
    autoImprove: false,
    creativityLevel: 5,
  });

  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const handleToggle = useCallback((field: keyof AISettings, value: boolean) => {
    setSettings(prev => ({ ...prev, [field]: value }));
    setHasChanges(true);
    setSaveError(null);
  }, []);

  const handleSelectChange = useCallback((field: keyof AISettings, value: any) => {
    setSettings(prev => ({ ...prev, [field]: value }));
    setHasChanges(true);
    setSaveError(null);
  }, []);

  const handleCreativityChange = useCallback((value: number) => {
    setSettings(prev => ({ ...prev, creativityLevel: value }));
    setHasChanges(true);
    setSaveError(null);
  }, []);

  // ============================================================================
  // AUTO-SAVE
  // ============================================================================

  useEffect(() => {
    if (!hasChanges) return;

    const timer = setTimeout(() => {
      handleSave();
    }, 2000);

    return () => clearTimeout(timer);
  }, [settings, hasChanges]);

  const handleSave = async () => {
    setIsSaving(true);
    setSaveError(null);

    try {
      await apiClient.put('/user/ai-preferences', settings);

      setSaveSuccess(true);
      setHasChanges(false);

      if (onSave) onSave();

      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error: any) {
      console.error('Failed to save AI preferences:', error);
      setSaveError(
        error.response?.data?.detail ||
        error.response?.data?.message ||
        'Failed to save preferences'
      );
    } finally {
      setIsSaving(false);
    }
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="space-y-6">
      {/* Auto-save Indicator */}
      {(isSaving || saveSuccess) && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            {isSaving ? (
              <>
                <Loader2 className="w-5 h-5 text-blue-600 dark:text-blue-400 animate-spin" />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Saving preferences...
                </span>
              </>
            ) : saveSuccess ? (
              <>
                <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />
                <span className="text-sm text-green-700 dark:text-green-300">
                  AI preferences saved automatically
                </span>
              </>
            ) : null}
          </div>
        </div>
      )}

      {/* Error Message */}
      {saveError && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3 text-red-600 dark:text-red-400">
            <AlertCircle className="w-5 h-5" />
            <span className="text-sm">{saveError}</span>
          </div>
        </div>
      )}

      {/* Tone Selection */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          AI Tone & Style
        </h3>

        <div className="space-y-3 mb-6">
          {TONE_OPTIONS.map((option) => (
            <label
              key={option.value}
              className={`
                block p-4 rounded-lg border-2 cursor-pointer transition-all
                ${settings.tone === option.value
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }
              `}
            >
              <div className="flex items-start gap-3">
                <input
                  type="radio"
                  name="tone"
                  value={option.value}
                  checked={settings.tone === option.value}
                  onChange={() => handleSelectChange('tone', option.value)}
                  className="mt-1 w-4 h-4 text-blue-600 focus:ring-2 focus:ring-blue-500"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <div className={settings.tone === option.value ? 'text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400'}>
                      {option.icon}
                    </div>
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      {option.label}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    {option.description}
                  </p>
                  <div className="text-xs italic text-gray-500 dark:text-gray-500 bg-gray-50 dark:bg-gray-900 p-2 rounded">
                    Example: "{option.example}"
                  </div>
                </div>
                {settings.tone === option.value && (
                  <Check className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-1" />
                )}
              </div>
            </label>
          ))}
        </div>

        {/* Writing Style */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Writing Style
          </label>
          <div className="grid grid-cols-3 gap-3">
            {[
              { value: 'concise' as const, label: 'Concise', description: 'Short & direct' },
              { value: 'detailed' as const, label: 'Detailed', description: 'Comprehensive' },
              { value: 'storytelling' as const, label: 'Storytelling', description: 'Narrative-driven' },
            ].map((style) => (
              <button
                key={style.value}
                type="button"
                onClick={() => handleSelectChange('writingStyle', style.value)}
                className={`
                  p-3 rounded-lg border-2 transition-all text-center
                  ${settings.writingStyle === style.value
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }
                `}
              >
                <div className="font-medium text-gray-900 dark:text-gray-100 text-sm">
                  {style.label}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                  {style.description}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Language */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Language Preferences
        </h3>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4" />
              <span>AI Content Language</span>
            </div>
          </label>
          <select
            value={settings.language}
            onChange={(e) => handleSelectChange('language', e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {LANGUAGE_OPTIONS.map((lang) => (
              <option key={lang.value} value={lang.value}>
                {lang.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* AI Features */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          AI-Powered Features
        </h3>

        <div>
          <Toggle
            icon={<Hash className="w-5 h-5" />}
            label="Auto Hashtags"
            description="Automatically suggest relevant hashtags for your posts"
            checked={settings.autoHashtags}
            onChange={(checked) => handleToggle('autoHashtags', checked)}
          />

          <Toggle
            icon={<Lightbulb className="w-5 h-5" />}
            label="Content Suggestions"
            description="Get AI-powered content ideas and improvements"
            checked={settings.contentSuggestions}
            onChange={(checked) => handleToggle('contentSuggestions', checked)}
            badge="Popular"
          />

          <Toggle
            icon={<Type className="w-5 h-5" />}
            label="Grammar Correction"
            description="Automatically fix grammar and spelling errors"
            checked={settings.grammarCorrection}
            onChange={(checked) => handleToggle('grammarCorrection', checked)}
          />

          <Toggle
            icon={<MessageSquare className="w-5 h-5" />}
            label="Tone Consistency"
            description="Maintain consistent tone across all content"
            checked={settings.toneConsistency}
            onChange={(checked) => handleToggle('toneConsistency', checked)}
          />

          <Toggle
            icon={<Sparkles className="w-5 h-5" />}
            label="Emoji Suggestions"
            description="Suggest relevant emojis to enhance engagement"
            checked={settings.emojiSuggestions}
            onChange={(checked) => handleToggle('emojiSuggestions', checked)}
          />

          <Toggle
            icon={<ImageIcon className="w-5 h-5" />}
            label="Image Descriptions"
            description="Auto-generate alt text for accessibility"
            checked={settings.imageDescriptions}
            onChange={(checked) => handleToggle('imageDescriptions', checked)}
          />
        </div>
      </div>

      {/* Content Optimization */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Content Optimization
        </h3>

        <div>
          <Toggle
            icon={<TrendingUp className="w-5 h-5" />}
            label="SEO Optimization"
            description="Optimize content for search engines"
            checked={settings.seoOptimization}
            onChange={(checked) => handleToggle('seoOptimization', checked)}
          />

          <Toggle
            icon={<Type className="w-5 h-5" />}
            label="Readability Enhancement"
            description="Improve text readability and clarity"
            checked={settings.readabilityEnhancement}
            onChange={(checked) => handleToggle('readabilityEnhancement', checked)}
          />

          <Toggle
            icon={<Zap className="w-5 h-5" />}
            label="Engagement Optimization"
            description="Maximize post engagement potential"
            checked={settings.engagementOptimization}
            onChange={(checked) => handleToggle('engagementOptimization', checked)}
            badge="Recommended"
          />
        </div>
      </div>

      {/* Advanced Settings */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Advanced Settings
        </h3>

        {/* Content Length */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Preferred Content Length
          </label>
          <div className="grid grid-cols-3 gap-3">
            {[
              { value: 'short' as const, label: 'Short', description: '50-100 words' },
              { value: 'medium' as const, label: 'Medium', description: '100-200 words' },
              { value: 'long' as const, label: 'Long', description: '200+ words' },
            ].map((length) => (
              <button
                key={length.value}
                type="button"
                onClick={() => handleSelectChange('contentLength', length.value)}
                className={`
                  p-3 rounded-lg border-2 transition-all text-center
                  ${settings.contentLength === length.value
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }
                `}
              >
                <div className="font-medium text-gray-900 dark:text-gray-100 text-sm">
                  {length.label}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                  {length.description}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Creativity Level */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4" />
                <span>AI Creativity Level</span>
              </div>
              <span className="text-blue-600 dark:text-blue-400 font-semibold">
                {settings.creativityLevel}/10
              </span>
            </div>
          </label>
          <input
            type="range"
            min="1"
            max="10"
            value={settings.creativityLevel}
            onChange={(e) => handleCreativityChange(Number(e.target.value))}
            className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
            style={{
              background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${settings.creativityLevel * 10}%, #e5e7eb ${settings.creativityLevel * 10}%, #e5e7eb 100%)`,
            }}
          />
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-2">
            <span>Conservative</span>
            <span>Balanced</span>
            <span>Experimental</span>
          </div>
        </div>

        {/* Auto-improve */}
        <Toggle
          icon={<Wand2 className="w-5 h-5" />}
          label="Auto-improve Content"
          description="Automatically enhance content quality before posting"
          checked={settings.autoImprove}
          onChange={(checked) => handleToggle('autoImprove', checked)}
        />
      </div>

      {/* Info Box */}
      <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-purple-600 dark:text-purple-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-purple-900 dark:text-purple-100">
            <p className="font-medium">✨ AI-Powered Content Creation</p>
            <p className="text-purple-700 dark:text-purple-300 mt-1">
              Our AI learns from your preferences to create content that matches your unique voice
              and style. Changes are saved automatically.
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

export default AIPreferences;
