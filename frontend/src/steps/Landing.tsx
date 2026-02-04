"use client";

import { useEffect, useRef, useState } from "react";
import { DotScreenShader } from "@/components/ui/dot-shader-background";
import { ContainerScroll } from "@/components/ui/container-scroll-animation";

export function Landing({ onStart }: { onStart: () => void }) {
  const pageRef = useRef<HTMLDivElement>(null);
  const [eventSource, setEventSource] = useState<HTMLElement | undefined>(undefined);

  useEffect(() => {
    setEventSource(pageRef.current ?? undefined);
  }, []);

  return (
    <div ref={pageRef} className="min-h-screen w-full bg-transparent text-neutral-900">
      {/* Dots background across the whole landing page */}
      <div className="fixed inset-0 z-0">
        <DotScreenShader eventSource={eventSource} />
      </div>

      {/* Hero */}
      <section className="relative z-10 min-h-[92vh] w-full overflow-hidden">
        <div className="mx-auto flex min-h-[92vh] w-full max-w-6xl flex-col justify-center px-6 py-14">
          <div className="max-w-3xl">
            <p className="mb-3 inline-flex items-center gap-2 rounded-full border border-neutral-200 bg-white/40 px-3 py-1 text-xs backdrop-blur">
              <span className="h-2 w-2 rounded-full bg-accent" />
              Evidence-grounded resume fit
            </p>

            <h1 className="text-5xl leading-[1.05] tracking-tight md:text-6xl">
              Get a role-fit report —{" "}
              <span className="relative inline-block">
                <span className="relative z-10">matched vs missing</span>
                <span className="absolute inset-x-0 bottom-[0.15em] z-0 h-[0.42em] rounded bg-accent/80" />
              </span>
              .
            </h1>

            <p className="mt-5 max-w-2xl text-base leading-relaxed text-neutral-700 md:text-lg">
              Stop guessing. Get a clear checklist of what you already match, what’s missing, and
              what evidence in your resume supports each claim.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
              <button
                onClick={onStart}
                className="inline-flex h-11 items-center justify-center rounded-md bg-accent px-5 text-sm font-semibold text-neutral-900 shadow-sm hover:bg-[#e6b400] focus:outline-none focus:ring-2 focus:ring-accent/50"
              >
                Start free
              </button>
              <div className="text-sm text-neutral-600">Local-only. No sign-up.</div>
            </div>
          </div>
        </div>
      </section>

      {/* Benefit-led section immediately under the hero */}
      <section className="relative z-10 mx-auto w-full max-w-6xl px-6 pb-14">
        <div className="grid gap-6 md:grid-cols-3">
          <div className="rounded-xl border border-neutral-200 bg-white/70 p-6 backdrop-blur">
            <div className="text-xs font-semibold tracking-wide text-neutral-500">SAVE TIME</div>
            <div className="mt-2 text-lg font-semibold">Focus on what moves the needle</div>
            <p className="mt-2 text-sm text-neutral-700">
              Turn a long JD into a short, actionable list—so you stop rewriting everything.
            </p>
          </div>
          <div className="rounded-xl border border-neutral-200 bg-white/70 p-6 backdrop-blur">
            <div className="text-xs font-semibold tracking-wide text-neutral-500">REDUCE RISK</div>
            <div className="mt-2 text-lg font-semibold">No invented “skills”</div>
            <p className="mt-2 text-sm text-neutral-700">
              Generated bullets are grounded in your own text, so you don’t accidentally claim what
              you can’t explain in interviews.
            </p>
          </div>
          <div className="rounded-xl border border-neutral-200 bg-white/70 p-6 backdrop-blur">
            <div className="text-xs font-semibold tracking-wide text-neutral-500">CLARITY</div>
            <div className="mt-2 text-lg font-semibold">Know what’s missing</div>
            <p className="mt-2 text-sm text-neutral-700">
              Get a “Need Info” checklist so you can fill gaps with real projects, metrics, and
              evidence.
            </p>
          </div>
        </div>
      </section>

      {/* Scroll section */}
      <section className="relative z-10">
        <ContainerScroll
          titleComponent={
            <div className="mx-auto max-w-4xl">
              <h2 className="text-3xl font-semibold tracking-tight text-neutral-900 md:text-5xl">
                From notes → a confident resume.
              </h2>
              <p className="mt-4 text-base text-neutral-700 md:text-lg">
                Start free → Sticker board → Target role → Analysis
              </p>
            </div>
          }
        >
          <div className="h-full w-full">
            <img
              src="https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=1600&q=80"
              alt="Workspace"
              className="h-full w-full rounded-2xl object-cover"
              draggable={false}
              loading="lazy"
            />
          </div>
        </ContainerScroll>
      </section>
    </div>
  );
}

