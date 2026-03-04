import { Shield, Code, Wrench, BookOpen, FileText } from 'lucide-react';
import { AnalysisResults } from '../types/analysis';

interface SummaryCardsProps {
  results: AnalysisResults;
}

export function SummaryCards({ results }: SummaryCardsProps) {
  const { summary } = results;

  const cards = [
    {
      title: 'Total Issues',
      value: summary.total_issues,
      icon: FileText,
      color: 'text-gray-600',
      bgColor: 'bg-gray-100',
    },
    {
      title: 'Security',
      value: summary.by_category.security,
      icon: Shield,
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    },
    {
      title: 'Code Smells',
      value: summary.by_category['code-smell'],
      icon: Code,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      title: 'Maintainability',
      value: summary.by_category.maintainability,
      icon: Wrench,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
    },
    {
      title: 'Readability',
      value: summary.by_category.readability,
      icon: BookOpen,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div
            key={card.title}
            className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">{card.title}</span>
              <div className={`p-2 rounded-lg ${card.bgColor}`}>
                <Icon className={`h-4 w-4 ${card.color}`} />
              </div>
            </div>
            <div className="text-3xl font-bold text-gray-900">{card.value}</div>
          </div>
        );
      })}
    </div>
  );
}
