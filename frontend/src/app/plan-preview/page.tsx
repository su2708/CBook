"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { useApi } from "../../hooks/useApi";
import { NonDraggableStudyPlan } from "../../components/nondraggable-study-plan";
import { StudyPlanItem } from "../../components/study-plan-item";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import type { DragEndEvent } from "@dnd-kit/core";
import { calculateDaysRemaining, formatDate } from "../../utils/date";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../../components/ui/dialog";
import { DialogDescription } from "@radix-ui/react-dialog";

interface StudyPlan {
  book_title: string;
  today: string;
  test_day: string;
  total_plan: {
    [key: string]: string[];
  };
}

interface PlanItem {
  id: string;
  type: "week" | "task";
  content: string;
  weekNumber: number;
}

export default function PlanPreviewPage() {
  const [studyPlan, setStudyPlan] = useState<StudyPlan | null>(null);
  const [planItems, setPlanItems] = useState<PlanItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [testName, setTestName] = useState("");
  const [testPlace, setTestPlace] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [nameError, setNameError] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const [chatId, setChatId] = useState<string | null>(null);
  const [isAddPlanDialogOpen, setIsAddPlanDialogOpen] = useState(false);
  const [newPlanName, setNewPlanName] = useState("");
  const [isDeleteMode, setIsDeleteMode] = useState(false);
  const router = useRouter();
  const { apiCall, isLoading } = useApi();

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  useEffect(() => {
    try {
      const planData = localStorage.getItem("studyPlan");
      const chatUrl = localStorage.getItem("chatUrl");

      if (chatUrl) {
        const urlParts = chatUrl.split("/");
        setUserId(urlParts[2]);
        setChatId(urlParts[3]);
      }

      if (planData) {
        const parsedPlan = JSON.parse(planData) as StudyPlan;
        if (
          parsedPlan &&
          typeof parsedPlan === "object" &&
          parsedPlan.book_title &&
          parsedPlan.test_day &&
          parsedPlan.total_plan
        ) {
          setStudyPlan(parsedPlan);

          const items: PlanItem[] = [];
          Object.entries(parsedPlan.total_plan).forEach(
            ([week, tasks], weekIndex) => {
              items.push({
                id: `week-${weekIndex + 1}`,
                type: "week",
                content: week,
                weekNumber: weekIndex + 1,
              });
              tasks.forEach((task, taskIndex) => {
                items.push({
                  id: `task-${weekIndex + 1}-${taskIndex + 1}`,
                  type: "task",
                  content: task,
                  weekNumber: weekIndex + 1,
                });
              });
            }
          );
          setPlanItems(items);
        } else {
          setError("유효하지 않은 학습 계획 데이터입니다.");
        }
      } else {
        setError("학습 계획을 찾을 수 없습니다.");
      }
    } catch (err) {
      console.error("학습 계획 파싱 오류:", err);
      setError("학습 계획을 불러오는 중 오류가 발생했습니다.");
    }
  }, []);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      setPlanItems((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id);
        const newIndex = items.findIndex((item) => item.id === over.id);

        // Prevent moving weeks
        if (items[oldIndex].type === "week") {
          return items;
        }

        return arrayMove(items, oldIndex, newIndex);
      });
    }
  };

  const handleSubmit = async () => {
    if (!testName.trim()) {
      setNameError(true);
      return;
    }
    setNameError(false);
    setIsSubmitting(true);

    if (!userId || !chatId) {
      setError("사용자 또는 채팅방 정보를 찾을 수 없습니다.");
      setIsSubmitting(false);
      return;
    }

    // Reconstruct the total_plan based on the current order of planItems
    const total_plan: { [key: string]: { task: string; is_done: boolean }[] } =
      {};
    let currentWeek = "";
    planItems.forEach((item) => {
      if (item.type === "week") {
        currentWeek = item.content;
        total_plan[currentWeek] = [];
      } else if (item.type === "task" && currentWeek) {
        total_plan[currentWeek].push({ task: item.content, is_done: false });
      }
    });

    const payload = {
      plan_id: chatId,
      test_name: testName,
      test_date: studyPlan?.test_day,
      test_place: testPlace || "어딘가",
      test_plan: {
        total_plan,
      },
      chatroom: chatId,
    };

    try {
      const { data, error, status } = await apiCall<{ message: string }>(
        `/api/v1/testplans/?user_id=${userId}&chatroom_id=${chatId}`,
        "POST",
        payload
      );

      if (error) {
        console.error("시험 계획 제출 실패:", error);
        setError("시험 계획 제출에 실패했습니다.");
      } else if (
        data &&
        data.message === "시험 계획 생성 성공" &&
        status === 201
      ) {
        router.push("/profile");
      } else {
        setError("예상치 못한 응답을 받았습니다.");
      }
    } catch (error) {
      console.error("시험 계획 제출 중 오류 발생:", error);
      setError("시험 계획 제출 중 오류가 발생했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAddNewPlan = () => {
    if (newPlanName.trim()) {
      const newPlanItem: PlanItem = {
        id: `task-new-${Date.now()}`,
        type: "task",
        content: newPlanName,
        weekNumber: 1, // 1주차에 해당
      };

      const week1Index = planItems.findIndex(
        (item) => item.type === "week" && item.weekNumber === 1
      );
      if (week1Index !== -1) {
        const newPlanItems = [...planItems];
        newPlanItems.splice(week1Index + 1, 0, newPlanItem);
        setPlanItems(newPlanItems);
      } else {
        setPlanItems([newPlanItem, ...planItems]);
      }
      setNewPlanName("");
      setIsAddPlanDialogOpen(false);
    }
  };

  if (error) {
    return (
      <div className="container max-w-2xl mx-auto p-4 space-y-6">
        <div className="text-center text-red-500">{error}</div>
        <Button className="w-full py-6" onClick={() => window.history.back()}>
          이전 화면으로 돌아가기
        </Button>
      </div>
    );
  }

  if (!studyPlan) {
    return (
      <div className="container max-w-2xl mx-auto p-4 space-y-6">
        <div className="text-center">학습 계획을 불러오는 중...</div>
      </div>
    );
  }

  const formattedToday = formatDate(studyPlan.today);
  const formattedTestDay = formatDate(studyPlan.test_day);

  return (
    <div className="container max-w-4xl mx-auto">
      <div className="sticky top-0 bg-background z-10 p-4 border-b">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">{studyPlan.book_title}</h1>
            <div className="flex justify-between items-center mt-2">
              <div className="text-sm">
                <span className="font-semibold">시험 날짜:</span>{" "}
                {formattedTestDay} (
                {calculateDaysRemaining(formattedTestDay, formattedToday)}일
                남음)
              </div>
            </div>
          </div>
          <Button
            variant="secondary"
            onClick={() => setIsDeleteMode(!isDeleteMode)}
          >
            {isDeleteMode ? "돌아가기" : "삭제 모드"}
          </Button>
        </div>
        <div className="mt-4 flex space-x-4">
          <div className="flex-1">
            <Input
              placeholder="시험 이름 (필수)"
              value={testName}
              onChange={(e) => setTestName(e.target.value)}
              className={nameError ? "border-red-500" : ""}
            />
            {nameError && (
              <p className="text-red-500 text-sm mt-2">
                시험 이름은 필수 항목입니다.
              </p>
            )}
          </div>
          <div className="flex-1">
            <Input
              placeholder="시험 장소 (선택)"
              value={testPlace}
              onChange={(e) => setTestPlace(e.target.value)}
            />
          </div>
        </div>
        <div className="flex space-x-4 mt-4">
          <Dialog
            open={isAddPlanDialogOpen}
            onOpenChange={setIsAddPlanDialogOpen}
          >
            <DialogTrigger asChild>
              <Button className="flex-1 py-4" variant="default">
                + 세부 시험계획 추가하기
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>세부 시험계획 추가</DialogTitle>
              </DialogHeader>
              <DialogDescription className="text-sm text-muted-foreground">
                1주차 최상단에 추가되며 직접 원하는 위치로 옮기면 됩니다.
              </DialogDescription>
              <Input
                placeholder="시험 계획 이름"
                value={newPlanName}
                onChange={(e) => setNewPlanName(e.target.value)}
              />
              <div className="flex justify-end mt-4">
                <Button onClick={handleAddNewPlan}>확인</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="flex-grow overflow-y-auto p-4">
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            disabled={isDeleteMode}
            items={planItems.map((item) => item.id)}
            strategy={verticalListSortingStrategy}
          >
            {planItems.map((item) =>
              item.type === "week" ? (
                <NonDraggableStudyPlan
                  key={item.id}
                  id={item.id}
                  week={item.content}
                />
              ) : (
                <StudyPlanItem
                  key={item.id}
                  id={item.id}
                  task={item.content}
                  isDeleteMode={isDeleteMode}
                  onDelete={() => {
                    setPlanItems(
                      planItems.filter((planItem) => planItem.id !== item.id)
                    );
                  }}
                />
              )
            )}
          </SortableContext>
        </DndContext>
      </div>

      <div className="sticky bottom-0 bg-background z-10 p-4 border-t">
        <div className="flex space-x-4">
          <Button
            className="flex-1 py-6"
            variant="secondary"
            onClick={() => window.history.back()}
          >
            이전 화면으로 돌아가기
          </Button>
          <Button
            className="flex-1 py-6"
            onClick={handleSubmit}
            disabled={isSubmitting || isLoading}
          >
            {isSubmitting || isLoading ? "제출 중..." : "확정하기"}
          </Button>
        </div>
      </div>
    </div>
  );
}
