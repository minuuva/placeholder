"use client";

// Force cache invalidation
import React from "react";
import { HeroSection } from "@/components/hero";
import {
  ProblemSection,
  HowItWorksSection,
  PreviewSection,
  ManifestoSection,
  PartnersSection,
  TeamSection,
  Footer,
} from "@/components/sections";

export default function Home() {
  return (
    <main className="bg-[#0a0a0f]">
      {/* Hero */}
      <HeroSection />

      {/* Section 1: The Problem */}
      <ProblemSection />

      {/* Section 2: How It Works */}
      <HowItWorksSection />

      {/* Section 3: Manifesto - monopo style text reveal */}
      <ManifestoSection />

      {/* Section 4: Live Preview */}
      <PreviewSection />

      {/* Section 5: Partners & Data Sources */}
      <PartnersSection />

      {/* Section 6: Team */}
      <TeamSection />

      {/* Footer */}
      <Footer />
    </main>
  );
}
