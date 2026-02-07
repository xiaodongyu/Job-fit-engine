import { useEffect, useLayoutEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

export type TourStep = {
  id: string;
  selector: string;
  title: string;
  body: string;
  padding?: number;
  placement?: "right" | "left" | "top" | "bottom" | "center";
};

type Rect = { top: number; left: number; width: number; height: number };

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

function getRectForSelector(selector: string, padding: number): Rect | null {
  const el = document.querySelector(selector) as HTMLElement | null;
  if (!el) return null;
  const r = el.getBoundingClientRect();
  const top = Math.max(8, r.top - padding);
  const left = Math.max(8, r.left - padding);
  const width = Math.min(window.innerWidth - left - 8, r.width + padding * 2);
  const height = Math.min(window.innerHeight - top - 8, r.height + padding * 2);
  return { top, left, width, height };
}

function getCardPosition(rect: Rect | null, placement: TourStep["placement"]) {
  const margin = 14;
  const w = 360;
  const h = 190;
  const vw = window.innerWidth;
  const vh = window.innerHeight;

  if (!rect || placement === "center") {
    return {
      top: Math.round((vh - h) / 2),
      left: Math.round((vw - w) / 2),
      width: w,
    };
  }

  const candidates: Record<string, { top: number; left: number }> = {
    right: {
      top: rect.top,
      left: rect.left + rect.width + margin,
    },
    left: {
      top: rect.top,
      left: rect.left - w - margin,
    },
    bottom: {
      top: rect.top + rect.height + margin,
      left: rect.left,
    },
    top: {
      top: rect.top - h - margin,
      left: rect.left,
    },
  };

  const p = placement ?? "bottom";
  const chosen = candidates[p];
  return {
    top: clamp(chosen.top, 12, vh - h - 12),
    left: clamp(chosen.left, 12, vw - w - 12),
    width: w,
  };
}

export function TutorialTour({
  open,
  steps,
  stepIndex,
  onStepIndexChange,
  onSkip,
  onEnd,
}: {
  open: boolean;
  steps: TourStep[];
  stepIndex: number;
  onStepIndexChange: (idx: number) => void;
  onSkip: () => void;
  onEnd: () => void;
}) {
  const step = steps[stepIndex];
  const padding = step?.padding ?? 10;

  const [rect, setRect] = useState<Rect | null>(null);

  const measure = () => {
    if (!step) return;
    setRect(getRectForSelector(step.selector, padding));
  };

  useLayoutEffect(() => {
    if (!open) return;
    measure();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, stepIndex]);

  useEffect(() => {
    if (!open) return;
    const onResize = () => measure();
    const onScroll = () => measure();
    window.addEventListener("resize", onResize);
    window.addEventListener("scroll", onScroll, true);
    return () => {
      window.removeEventListener("resize", onResize);
      window.removeEventListener("scroll", onScroll, true);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, stepIndex]);

  const cardPos = useMemo(() => getCardPosition(rect, step?.placement), [rect, step]);

  const isLast = stepIndex >= steps.length - 1;
  const nextLabel = isLast ? "End" : "Next";

  const handleNext = () => {
    if (isLast) {
      onEnd();
      return;
    }
    onStepIndexChange(stepIndex + 1);
  };

  return (
    <AnimatePresence>
      {open && step && (
        <motion.div
          className="fixed inset-0 z-[9999]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.18 }}
        >
          {/* Dim + blur */}
          <div className="absolute inset-0 bg-black/55 backdrop-blur-[2px]" />

          {/* Spotlight */}
          {rect && (
            <motion.div
              className="absolute rounded-xl"
              style={{
                top: rect.top,
                left: rect.left,
                width: rect.width,
                height: rect.height,
                boxShadow: "0 0 0 9999px rgba(0,0,0,0.55)",
                border: "1px solid rgba(255,199,0,0.55)",
                background: "transparent",
                pointerEvents: "none",
              }}
              initial={false}
              animate={{
                top: rect.top,
                left: rect.left,
                width: rect.width,
                height: rect.height,
              }}
              transition={{ type: "spring", stiffness: 260, damping: 30 }}
            />
          )}

          {/* Card */}
          <motion.div
            className="absolute rounded-xl border border-neutral-200 bg-white p-5 shadow-xl"
            style={{ top: cardPos.top, left: cardPos.left, width: cardPos.width }}
            initial={{ opacity: 0, y: 10, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.98 }}
            transition={{ duration: 0.18 }}
          >
            <div className="text-xs font-semibold tracking-wide text-neutral-500">
              Tutorial • {stepIndex + 1}/{steps.length}
            </div>
            <div className="mt-2 text-base font-semibold text-neutral-900">{step.title}</div>
            <div className="mt-2 text-sm leading-relaxed text-neutral-700">{step.body}</div>

            <div className="mt-4 flex items-center justify-between">
              <button
                onClick={onSkip}
                className="text-sm font-medium text-neutral-600 hover:text-neutral-900"
              >
                Skip
              </button>
              <button
                onClick={handleNext}
                className="inline-flex h-9 items-center justify-center rounded-md bg-accent px-4 text-sm font-semibold text-neutral-900 hover:bg-[#e6b400]"
              >
                {nextLabel}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

