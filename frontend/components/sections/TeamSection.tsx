"use client";

import React, { useEffect, useRef } from "react";
import Image from "next/image";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const TEAM_MEMBERS = [
  {
    name: "Adam Carlson",
    role: "Physics & Math",
    year: "3rd Year @ UVA",
    company: "Susquehanna International Group",
    location: "Williamsburg, Virginia",
    image: "/team-adam.jpg",
  },
  {
    name: "Minu Choi",
    role: "Data Science",
    year: "3rd Year @ UVA",
    company: "Grid",
    location: "Seoul, South Korea",
    image: "/team-minu.jpg",
  },
  {
    name: "Otso Karali",
    role: "Math & Computer Science",
    year: "3rd Year @ UVA",
    company: "DRW Trading",
    location: "Helsinki, Finland",
    image: "/team-otso.png",
  },
];

export function TeamSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const headlineRef = useRef<HTMLHeadingElement>(null);
  const cardsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!sectionRef.current) return;

    const ctx = gsap.context(() => {
      gsap.set([headlineRef.current, cardsRef.current], {
        opacity: 0,
        y: 60,
      });

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top 80%",
          toggleActions: "play none none none",
        },
      });

      tl.to(headlineRef.current, {
        opacity: 1,
        y: 0,
        duration: 1,
        ease: "power3.out",
      }).to(
        cardsRef.current,
        {
          opacity: 1,
          y: 0,
          duration: 0.8,
          ease: "power3.out",
        },
        "-=0.5"
      );

      // Stagger team cards
      gsap.from(".team-card", {
        scrollTrigger: {
          trigger: cardsRef.current,
          start: "top 85%",
        },
        opacity: 0,
        y: 40,
        stagger: 0.15,
        duration: 0.8,
        ease: "power3.out",
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      className="relative w-full pt-12 pb-16 px-8 md:px-16 lg:px-24 overflow-hidden"
    >
      {/* Background gradient */}
      <div
        className="absolute right-0 top-1/2 -translate-y-1/2 w-[600px] h-[600px] pointer-events-none"
        style={{
          background: "radial-gradient(circle at center, rgba(255,159,64,0.05) 0%, transparent 60%)",
          filter: "blur(60px)",
        }}
      />

      {/* Section label */}
      <div className="section-label mb-10">
        <span>The Team</span>
      </div>

      {/* Headline */}
      <h2
        ref={headlineRef}
        className="font-display text-4xl md:text-5xl lg:text-[4rem] font-bold leading-[1.05] tracking-[-0.03em] mb-16"
      >
        <span className="text-white">Built by</span>
        <br />
        <span className="text-gradient-accent">UVA students.</span>
      </h2>

      {/* Team cards */}
      <div ref={cardsRef} className="grid md:grid-cols-3 gap-8 max-w-5xl">
        {TEAM_MEMBERS.map((member) => (
          <div
            key={member.name}
            className="team-card group relative p-6 rounded-2xl bg-white/[0.02] border border-white/[0.06] hover:border-white/[0.12] hover:bg-white/[0.04] transition-all duration-300"
          >
            {/* Photo */}
            <div className="relative w-24 h-24 mx-auto mb-6 rounded-2xl overflow-hidden bg-white/[0.05]">
              <Image
                src={member.image}
                alt={member.name}
                fill
                className="object-cover"
              />
            </div>

            {/* Name */}
            <h3 className="text-xl font-display font-semibold text-white text-center mb-1">
              {member.name}
            </h3>

            {/* Role & Year */}
            <p className="text-sm text-white/50 text-center mb-4">
              {member.role} &middot; {member.year}
            </p>

            {/* Company & Location */}
            <div className="space-y-2">
              <div className="flex items-center justify-center gap-2 text-xs text-white/40">
                <svg className="w-3.5 h-3.5 text-amber-400/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                <span>{member.company}</span>
              </div>
              <div className="flex items-center justify-center gap-2 text-xs text-white/40">
                <svg className="w-3.5 h-3.5 text-amber-400/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span>{member.location}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export default TeamSection;
