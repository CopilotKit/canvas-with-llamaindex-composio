"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import Link from "next/link";
import { ArrowLeft, Download, Send } from "lucide-react";
import { useCopilotAction } from "@copilotkit/react-core";

interface AssessmentCriteria {
  id: string;
  category: string;
  criteria: string;
  description: string;
  score: number;
  weight: number;
}

interface PitchAssessment {
  sellerId: string;
  sellerName: string;
  companyId: string;
  companyName: string;
  date: string;
  overallScore: number;
  criteria: AssessmentCriteria[];
  feedback: string;
  recommendation: "highly_recommend" | "recommend" | "neutral" | "not_recommend";
}

export default function PitchScorePage() {
  const searchParams = useSearchParams();
  const companyId = searchParams.get("company") || "1";

  const [assessment, setAssessment] = useState<PitchAssessment>({
    sellerId: "seller-1",
    sellerName: "John Smith",
    companyId,
    companyName: "TechCorp Solutions",
    date: new Date().toISOString().split("T")[0],
    overallScore: 0,
    criteria: [
      {
        id: "1",
        category: "Product Knowledge",
        criteria: "Understanding of Product/Service",
        description: "Demonstrates deep knowledge of features, benefits, and use cases",
        score: 0,
        weight: 20,
      },
      {
        id: "2",
        category: "Communication",
        criteria: "Clarity and Articulation",
        description: "Communicates ideas clearly and adapts message to audience",
        score: 0,
        weight: 15,
      },
      {
        id: "3",
        category: "Needs Analysis",
        criteria: "Understanding Customer Needs",
        description: "Asks relevant questions and identifies pain points accurately",
        score: 0,
        weight: 20,
      },
      {
        id: "4",
        category: "Solution Fit",
        criteria: "Relevance of Proposed Solution",
        description: "Aligns solution with specific company needs and challenges",
        score: 0,
        weight: 20,
      },
      {
        id: "5",
        category: "Objection Handling",
        criteria: "Addressing Concerns",
        description: "Handles objections professionally and provides satisfactory answers",
        score: 0,
        weight: 15,
      },
      {
        id: "6",
        category: "Professionalism",
        criteria: "Overall Professionalism",
        description: "Maintains professional demeanor, punctuality, and follow-up",
        score: 0,
        weight: 10,
      },
    ],
    feedback: "",
    recommendation: "neutral",
  });

  // Calculate overall score
  const calculateOverallScore = () => {
    const totalScore = assessment.criteria.reduce((sum, criterion) => {
      return sum + (criterion.score * criterion.weight) / 100;
    }, 0);
    return Math.round(totalScore);
  };

  // Update criterion score
  const updateScore = (criterionId: string, score: number) => {
    setAssessment(prev => ({
      ...prev,
      criteria: prev.criteria.map(c =>
        c.id === criterionId ? { ...c, score } : c
      ),
      overallScore: calculateOverallScore(),
    }));
  };

  // CopilotKit action to help with assessment
  useCopilotAction({
    name: "suggest_feedback",
    description: "Suggest constructive feedback based on the scores",
    parameters: [
      {
        name: "scores",
        type: "object",
        description: "The current assessment scores",
        required: true,
      },
    ],
    handler: async ({ scores }) => {
      // Generate feedback based on scores
      const feedback = "Based on the scores, the seller showed strong product knowledge but could improve on needs analysis...";
      setAssessment(prev => ({ ...prev, feedback }));
      return "Feedback suggestion added";
    },
  });

  const getRecommendationColor = (recommendation: PitchAssessment["recommendation"]) => {
    switch (recommendation) {
      case "highly_recommend":
        return "text-green-600";
      case "recommend":
        return "text-blue-600";
      case "neutral":
        return "text-yellow-600";
      case "not_recommend":
        return "text-red-600";
    }
  };

  const overallScore = calculateOverallScore();

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <Link href={`/company/${companyId}`}>
            <Button variant="ghost" size="sm" className="gap-2 mb-4">
              <ArrowLeft className="h-4 w-4" />
              Back to Company Details
            </Button>
          </Link>
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">Seller's Pitch Score</h1>
              <p className="text-muted-foreground mt-1">
                Evaluate {assessment.sellerName}'s pitch to {assessment.companyName}
              </p>
            </div>
            <div className="text-right">
              <div className="text-4xl font-bold">{overallScore}%</div>
              <p className="text-sm text-muted-foreground">Overall Score</p>
            </div>
          </div>
        </div>

        {/* Assessment Criteria */}
        <div className="space-y-6 mb-8">
          {assessment.criteria.map((criterion) => (
            <div key={criterion.id} className="rounded-lg border bg-card p-6">
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold">{criterion.criteria}</h3>
                  <span className="text-sm text-muted-foreground">
                    Weight: {criterion.weight}%
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">{criterion.description}</p>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span>Score</span>
                  <span className="font-medium">{criterion.score}/10</span>
                </div>
                <div className="flex gap-2">
                  {[...Array(10)].map((_, i) => (
                    <button
                      key={i}
                      onClick={() => updateScore(criterion.id, i + 1)}
                      className={`h-8 w-8 rounded border transition-colors ${
                        criterion.score >= i + 1
                          ? "bg-primary text-primary-foreground"
                          : "bg-background hover:bg-secondary"
                      }`}
                    >
                      {i + 1}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Overall Assessment */}
        <div className="rounded-lg border bg-card p-6 mb-6">
          <h3 className="font-semibold mb-4">Overall Assessment</h3>
          
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Total Score</span>
              <span className="text-2xl font-bold">{overallScore}%</span>
            </div>
            <Progress value={overallScore} className="h-3" />
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Recommendation
              </label>
              <select
                className="w-full rounded-md border px-3 py-2"
                value={assessment.recommendation}
                onChange={(e) =>
                  setAssessment(prev => ({
                    ...prev,
                    recommendation: e.target.value as PitchAssessment["recommendation"],
                  }))
                }
              >
                <option value="highly_recommend">Highly Recommend</option>
                <option value="recommend">Recommend</option>
                <option value="neutral">Neutral</option>
                <option value="not_recommend">Do Not Recommend</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                Additional Feedback
              </label>
              <textarea
                className="w-full rounded-md border px-3 py-2 min-h-[100px]"
                placeholder="Provide constructive feedback for the seller..."
                value={assessment.feedback}
                onChange={(e) =>
                  setAssessment(prev => ({ ...prev, feedback: e.target.value }))
                }
              />
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-4">
          <Button className="flex-1" size="lg">
            <Send className="h-4 w-4 mr-2" />
            Submit Assessment
          </Button>
          <Button variant="outline" size="lg">
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
        </div>

        {/* Recent Assessments */}
        <div className="mt-12">
          <h2 className="text-xl font-semibold mb-4">Recent Assessments</h2>
          <div className="space-y-3">
            <div className="rounded-lg border bg-card p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Jane Doe - FinanceTech Corp</p>
                  <p className="text-sm text-muted-foreground">2 days ago</p>
                </div>
                <div className="text-right">
                  <p className="font-bold">85%</p>
                  <p className={`text-sm ${getRecommendationColor("highly_recommend")}`}>
                    Highly Recommend
                  </p>
                </div>
              </div>
            </div>
            <div className="rounded-lg border bg-card p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Mike Johnson - RetailMax</p>
                  <p className="text-sm text-muted-foreground">5 days ago</p>
                </div>
                <div className="text-right">
                  <p className="font-bold">72%</p>
                  <p className={`text-sm ${getRecommendationColor("recommend")}`}>
                    Recommend
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
