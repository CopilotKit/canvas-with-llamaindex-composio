"use client";

import { use } from "react";
import { useCoAgent, useCopilotAction, useCopilotAdditionalInstructions } from "@copilotkit/react-core";
import { CopilotKitCSSProperties, CopilotChat } from "@copilotkit/react-ui";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Building2, Users, Briefcase, Globe, Target, ArrowLeft } from "lucide-react";
import { cn } from "@/lib/utils";

interface PageProps {
  params: Promise<{
    id: string;
  }>;
}

interface CompanyDetails {
  id: string;
  name: string;
  industry: string;
  employees: string;
  website: string;
  description: string;
  jobOpenings: number;
  needs: string[];
  challenges: string[];
  currentSolutions: string[];
  decisionMakers: {
    name: string;
    role: string;
    focus: string;
  }[];
}

// Mock company data - in real app, fetch from API
const getCompanyDetails = (id: string): CompanyDetails => ({
  id,
  name: "TechCorp Solutions",
  industry: "Software Development",
  employees: "500-1000",
  website: "www.techcorp.com",
  description: "A leading software development company specializing in enterprise solutions, cloud computing, and AI-driven applications.",
  jobOpenings: 12,
  needs: [
    "Cloud infrastructure optimization",
    "DevOps tooling and automation",
    "Cybersecurity solutions",
    "Employee training platforms",
  ],
  challenges: [
    "Scaling development teams efficiently",
    "Maintaining code quality at scale",
    "Reducing time-to-market for new features",
    "Managing multi-cloud environments",
  ],
  currentSolutions: [
    "AWS for cloud hosting",
    "Jenkins for CI/CD",
    "Slack for communication",
    "Jira for project management",
  ],
  decisionMakers: [
    { name: "Sarah Johnson", role: "CTO", focus: "Technology strategy and innovation" },
    { name: "Mike Chen", role: "VP Engineering", focus: "Development processes and team efficiency" },
    { name: "Lisa Brown", role: "Director of IT", focus: "Infrastructure and security" },
  ],
});

export default function CompanyDetailsPage({ params }: PageProps) {
  const { id } = use(params);
  const company = getCompanyDetails(id);

  // Add company context to the AI
  useCopilotAdditionalInstructions(
    `You are helping a seller pitch to ${company.name}, a ${company.industry} company with ${company.employees} employees. 
    The company's main needs are: ${company.needs.join(", ")}.
    Their current challenges include: ${company.challenges.join(", ")}.
    Key decision makers are: ${company.decisionMakers.map(dm => `${dm.name} (${dm.role})`).join(", ")}.
    
    Help the seller craft effective pitches, handle objections, and close deals. Be consultative and focus on solving the company's specific problems.`
  );

  // Define actions for the pitch process
  useCopilotAction({
    name: "analyze_company_need",
    description: "Analyze a specific company need and suggest how to address it",
    parameters: [
      {
        name: "need",
        type: "string",
        description: "The specific need to analyze",
        required: true,
      },
    ],
    handler: async ({ need }) => {
      return `Analyzing ${need} for ${company.name}...`;
    },
  });

  useCopilotAction({
    name: "generate_pitch_opener",
    description: "Generate an effective pitch opener for this company",
    parameters: [
      {
        name: "decision_maker",
        type: "string",
        description: "The decision maker you're pitching to",
        required: true,
      },
    ],
    handler: async ({ decision_maker }) => {
      return `Generated opener for ${decision_maker} at ${company.name}`;
    },
  });

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link href="/companies">
            <Button variant="ghost" size="sm" className="gap-2">
              <ArrowLeft className="h-4 w-4" />
              Back to Companies
            </Button>
          </Link>
          <Link href={`/pitch-score?company=${id}`}>
            <Button size="sm">View Pitch Scores</Button>
          </Link>
        </div>
      </div>

      <div className="flex h-[calc(100vh-73px)]">
        {/* Chat Section - Left Side */}
        <div className="w-1/2 border-r">
          <CopilotChat
            className="h-full"
            instructions={`You are a sales coaching AI helping sellers pitch to ${company.name}. Guide them through the pitch process, help them handle objections, and close deals.`}
            labels={{
              title: `Pitch Assistant - ${company.name}`,
              initial: `Welcome! I'm here to help you pitch to ${company.name}. What product or service are you selling, and which decision maker are you targeting?`,
            }}
          />
        </div>

        {/* Company Details - Right Side */}
        <div className="w-1/2 overflow-y-auto p-6">
          <div className="max-w-2xl mx-auto space-y-6">
            {/* Company Header */}
            <div className="flex items-start gap-4">
              <Building2 className="h-12 w-12 text-muted-foreground mt-1" />
              <div className="flex-1">
                <h1 className="text-2xl font-bold">{company.name}</h1>
                <p className="text-muted-foreground">{company.industry}</p>
                <div className="flex items-center gap-4 mt-2 text-sm">
                  <span className="flex items-center gap-1">
                    <Users className="h-4 w-4" />
                    {company.employees}
                  </span>
                  <span className="flex items-center gap-1">
                    <Globe className="h-4 w-4" />
                    {company.website}
                  </span>
                  <span className="flex items-center gap-1">
                    <Briefcase className="h-4 w-4" />
                    {company.jobOpenings} openings
                  </span>
                </div>
              </div>
            </div>

            {/* Company Description */}
            <div className="rounded-lg border bg-card p-4">
              <h3 className="font-semibold mb-2">About</h3>
              <p className="text-sm text-muted-foreground">{company.description}</p>
            </div>

            {/* Company Needs */}
            <div className="rounded-lg border bg-card p-4">
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <Target className="h-5 w-5" />
                Current Needs
              </h3>
              <ul className="space-y-2">
                {company.needs.map((need, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm">
                    <span className="text-green-500 mt-0.5">•</span>
                    <span>{need}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Challenges */}
            <div className="rounded-lg border bg-card p-4">
              <h3 className="font-semibold mb-3">Pain Points & Challenges</h3>
              <ul className="space-y-2">
                {company.challenges.map((challenge, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm">
                    <span className="text-red-500 mt-0.5">•</span>
                    <span>{challenge}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Current Solutions */}
            <div className="rounded-lg border bg-card p-4">
              <h3 className="font-semibold mb-3">Current Tech Stack</h3>
              <div className="flex flex-wrap gap-2">
                {company.currentSolutions.map((solution, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center rounded-md bg-secondary px-2.5 py-0.5 text-sm"
                  >
                    {solution}
                  </span>
                ))}
              </div>
            </div>

            {/* Decision Makers */}
            <div className="rounded-lg border bg-card p-4">
              <h3 className="font-semibold mb-3">Key Decision Makers</h3>
              <div className="space-y-3">
                {company.decisionMakers.map((person, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <div className="h-10 w-10 rounded-full bg-secondary flex items-center justify-center">
                      <span className="text-sm font-medium">
                        {person.name.split(" ").map(n => n[0]).join("")}
                      </span>
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-sm">{person.name}</p>
                      <p className="text-xs text-muted-foreground">{person.role}</p>
                      <p className="text-xs text-muted-foreground mt-1">Focus: {person.focus}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
