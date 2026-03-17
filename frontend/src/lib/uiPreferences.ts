export type UiThemeMode = 'system' | 'light' | 'dark';
export type UiLocale = 'en' | 'ru' | 'de' | 'fr';
export type ResolvedTheme = 'light' | 'dark';

const THEME_STORAGE_KEY = 'ui.themeMode';
const LOCALE_STORAGE_KEY = 'ui.locale';

function canUseBrowser(): boolean {
  return typeof window !== 'undefined';
}

export function readThemeModePreference(): UiThemeMode {
  if (!canUseBrowser()) return 'system';
  const value = (window.localStorage.getItem(THEME_STORAGE_KEY) || '').trim().toLowerCase();
  if (value === 'light' || value === 'dark' || value === 'system') return value;
  return 'system';
}

export function writeThemeModePreference(mode: UiThemeMode): void {
  if (!canUseBrowser()) return;
  window.localStorage.setItem(THEME_STORAGE_KEY, mode);
}

export function resolveSystemTheme(): ResolvedTheme {
  if (!canUseBrowser() || typeof window.matchMedia !== 'function') return 'dark';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function resolveThemeMode(mode: UiThemeMode): ResolvedTheme {
  return mode === 'system' ? resolveSystemTheme() : mode;
}

export function readLocalePreference(): UiLocale | 'auto' {
  if (!canUseBrowser()) return 'auto';
  const value = (window.localStorage.getItem(LOCALE_STORAGE_KEY) || '').trim().toLowerCase();
  if (value === 'en' || value === 'ru' || value === 'de' || value === 'fr' || value === 'auto') return value;
  return 'auto';
}

export function writeLocalePreference(locale: UiLocale | 'auto'): void {
  if (!canUseBrowser()) return;
  window.localStorage.setItem(LOCALE_STORAGE_KEY, locale);
}

export function resolveSystemLocale(): UiLocale {
  if (!canUseBrowser()) return 'en';
  const langs = Array.isArray(window.navigator.languages) ? window.navigator.languages : [];
  const pool = [...langs, window.navigator.language].filter(Boolean).map((x) => String(x).toLowerCase());
  if (pool.some((x) => x.startsWith('ru'))) return 'ru';
  if (pool.some((x) => x.startsWith('de'))) return 'de';
  if (pool.some((x) => x.startsWith('fr'))) return 'fr';
  return 'en';
}

export function resolveLocale(mode: UiLocale | 'auto'): UiLocale {
  return mode === 'auto' ? resolveSystemLocale() : mode;
}
