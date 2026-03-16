import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Clock, BookOpen, BarChart } from "lucide-react";
import { Course } from "@/data/mentors";

interface CourseCardProps {
  course: Course;
}

const CourseCard = ({ course }: CourseCardProps) => {
  const getLevelColor = (level: string) => {
    switch (level) {
      case "Beginner":
        return "bg-green-500/10 text-green-700 border-green-500/20";
      case "Intermediate":
        return "bg-blue-500/10 text-blue-700 border-blue-500/20";
      case "Advanced":
        return "bg-purple-500/10 text-purple-700 border-purple-500/20";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  return (
    <Card className="group hover:shadow-strong transition-all duration-300 hover:-translate-y-1 overflow-hidden">
      <div className="h-48 overflow-hidden bg-muted">
        <img
          src={course.thumbnail}
          alt={course.title}
          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
        />
      </div>
      
      <CardContent className="p-6 space-y-4">
        <div>
          <Badge className={getLevelColor(course.level)} variant="outline">
            {course.level}
          </Badge>
        </div>

        <h3 className="text-xl font-display font-bold line-clamp-2">
          {course.title}
        </h3>

        <p className="text-sm text-muted-foreground line-clamp-2">
          {course.description}
        </p>

        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-1">
            <Clock size={16} />
            <span>{course.duration}</span>
          </div>
          <div className="flex items-center gap-1">
            <BookOpen size={16} />
            <span>{course.lessons} lessons</span>
          </div>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-border">
          <div>
            <div className="text-2xl font-display font-bold">
              ${course.price}
            </div>
            <div className="text-xs text-muted-foreground">one-time payment</div>
          </div>
          <Button variant="hero" size="sm">
            Enroll Now
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default CourseCard;