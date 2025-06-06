// src/features/notifications/useNotifier.ts
import { toast as sonnerToast } from "sonner"; // Using sonner for toasts via Shadcn
import { useAppStore } from '@/store/appStore';

export function useNotifier() {
  const voiceEnabled = useAppStore((state) => state.voiceAnnouncementsEnabled);

  const notify = (
    title: string,
    description?: string,
    type: 'success' | 'error' | 'info' | 'warning' | 'default' = 'default'
  ) => {
    console.log(`Notification (${type}): ${title} - ${description}`);

    const options = description ? { description } : {};

    if (type === 'success') sonnerToast.success(title, options);
    else if (type === 'error') sonnerToast.error(title, options);
    else if (type === 'warning') sonnerToast.warning(title, options);
    else if (type === 'info') sonnerToast.info(title, options);
    else sonnerToast(title, options);

    if (voiceEnabled && window.speechSynthesis) {
      if (!speechSynthesis.speaking) {
        const utterance = new SpeechSynthesisUtterance(description ? `${title}. ${description}` : title);
        speechSynthesis.speak(utterance);
      }
    }
  };
  return { notify };
}