import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DollarSign, Users, Star, Calendar } from "lucide-react";

interface MentorStatsCardProps {
  totalEarnings: number;
  totalStudents: number;
  averageRating: number;
  upcomingSessions: number;
}

export const MentorStatsCard = ({ 
  totalEarnings, 
  totalStudents, 
  averageRating, 
  upcomingSessions 
}: MentorStatsCardProps) => {
  const stats = [
    {
      title: "Total Earnings",
      value: `$${totalEarnings.toFixed(2)}`,
      icon: DollarSign,
      description: "Net after fees"
    },
    {
      title: "Total Students",
      value: totalStudents,
      icon: Users,
      description: "Students mentored"
    },
    {
      title: "Average Rating",
      value: averageRating > 0 ? averageRating.toFixed(1) : "N/A",
      icon: Star,
      description: "From student reviews"
    },
    {
      title: "Upcoming Sessions",
      value: upcomingSessions,
      icon: Calendar,
      description: "Sessions scheduled"
    }
  ];

  return (
    <div className="grid gap-3 sm:gap-4 grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <Card key={stat.title} className="overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 p-3 sm:p-4 pb-1 sm:pb-2">
              <CardTitle className="text-xs sm:text-sm font-medium truncate pr-2">
                {stat.title}
              </CardTitle>
              <Icon className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-muted-foreground shrink-0" />
            </CardHeader>
            <CardContent className="p-3 sm:p-4 pt-0 sm:pt-0">
              <div className="text-lg sm:text-2xl font-bold truncate">{stat.value}</div>
              <p className="text-[10px] sm:text-xs text-muted-foreground truncate">
                {stat.description}
              </p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};
