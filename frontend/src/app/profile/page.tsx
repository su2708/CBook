"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Settings,
  LogOut,
  User,
  Trash2,
  MoreHorizontal,
  PencilIcon,
} from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "../../components/ui/avatar";
import { useAuth } from "../../contexts/AuthContext";
import { useApi } from "../../hooks/useApi";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../../components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../../components/ui/alert-dialog";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "../../components/ui/popover";

import { formatDate } from "../../utils/date";
import { ModeToggle } from "../../components/theme-toggle";
import { Skeleton } from "../../components/ui/skeleton";

interface OngoingExam {
  id: number;
  plan_id: number;
  ctrm_id: number;
  title: string;
  daysRemaining: number;
  examDate: string;
  test_name: string;
  test_place: string;
  test_date: string;
}

interface UserProfile {
  id: number;
  username: string;
  email: string;
  phone: string | null;
  profile_image: string | null;
}

interface ChatRoom {
  id: number;
  chat_id: number;
  chat_name: string;
  created_at: string;
  updated_at: string;
  user_id: number;
  testplan: number | null;
}

interface ChatRoomResponse {
  message: string;
  data: {
    id: number;
    chat_id: number;
    chat_name: string;
    created_at: string;
    updated_at: string;
    user_id: number;
    testplan: null;
  };
}

interface Achievement {
  id: number;
  plan_id: number;
  user_id: number;
  test_name: string;
  test_date: string;
  test_place: string;
  created_at: string;
}

interface EditDialogProps {
  isOpen: boolean;
  onClose: () => void;
  fieldName: "username" | "email";
  currentValue: string;
  onSubmit: (value: string) => Promise<void>;
  error?: string;
}

function EditDialog({
  isOpen,
  onClose,
  fieldName,
  currentValue,
  onSubmit,
  error,
}: EditDialogProps) {
  const [value, setValue] = useState(currentValue);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await onSubmit(value);
      // Dialog closure is now handled in the parent component
    } catch (error) {
      // Just finish submitting state, don't close dialog
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AlertDialog open={isOpen} onOpenChange={onClose}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            {fieldName === "username" ? "사용자 이름 수정" : "이메일 수정"}
          </AlertDialogTitle>
        </AlertDialogHeader>
        <div className="space-y-4 py-4">
          <Input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={fieldName === "username" ? "사용자 이름" : "이메일"}
          />
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={onClose}>취소</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleSubmit}
            disabled={isSubmitting || !value.trim() || value === currentValue}
          >
            저장
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

export default function ProfilePage() {
  const { checkAuth, logout } = useAuth();
  const router = useRouter();
  const { apiCall, isLoading } = useApi();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [ongoingExams, setOngoingExams] = useState<OngoingExam[]>([]);
  const [showLogoutDialog, setShowLogoutDialog] = useState(false);
  const [showNewExamDialog, setShowNewExamDialog] = useState(false);
  const [newExamName, setNewExamName] = useState("");
  const [chatRooms, setChatRooms] = useState<ChatRoom[]>([]);
  const [isLoadingExams, setIsLoadingExams] = useState(true);
  const [isLoadingChatRooms, setIsLoadingChatRooms] = useState(true);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deletingItem, setDeletingItem] = useState<
    OngoingExam | ChatRoom | null
  >(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteMessage, setDeleteMessage] = useState("");
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [isLoadingAchievements, setIsLoadingAchievements] = useState(true);
  const [showProfileDialog, setShowProfileDialog] = useState(false);
  const [isLoadingProfileDetails, setIsLoadingProfileDetails] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editingField, setEditingField] = useState<"username" | "email" | null>(
    null
  );
  const [editError, setEditError] = useState<string>("");
  const [showWithdrawalDialog, setShowWithdrawalDialog] = useState(false);
  const [withdrawalPassword, setWithdrawalPassword] = useState("");
  const [withdrawalError, setWithdrawalError] = useState("");
  const [isWithdrawing, setIsWithdrawing] = useState(false);

  useEffect(() => {
    if (!checkAuth()) {
      router.push("/login");
    } else {
      fetchProfileData();
    }
  }, []);

  const fetchProfileData = async () => {
    try {
      const profileResponse = await apiCall<UserProfile>(
        "/api/v1/accounts/profile/",
        "GET"
      );

      if (profileResponse.error) {
        console.error("Failed to fetch profile:", profileResponse.error);
      } else if (profileResponse.data) {
        setProfile(profileResponse.data);

        const [examsResponse, chatRoomsResponse, achievementsResponse] =
          await Promise.all([
            apiCall<OngoingExam[]>(
              `/api/v1/testplans/?user_id=${profileResponse.data.id}`,
              "GET"
            ),
            apiCall<ChatRoom[]>(
              `/api/v1/chatrooms/?user_id=${profileResponse.data.id}`,
              "GET"
            ),
            apiCall<Achievement[]>(
              `/api/v1/archievements/?user_id=${profileResponse.data.id}`,
              "GET"
            ),
          ]);

        setIsLoadingExams(false);
        setIsLoadingChatRooms(false);
        setIsLoadingAchievements(false);

        if (examsResponse.error) {
          console.error("Failed to fetch ongoing exams:", examsResponse.error);
        } else if (examsResponse.data) {
          setOngoingExams(examsResponse.data);
        }

        if (chatRoomsResponse.error) {
          console.error("Failed to fetch chat rooms:", chatRoomsResponse.error);
        } else if (chatRoomsResponse.data) {
          setChatRooms(chatRoomsResponse.data);
        }

        if (achievementsResponse.error) {
          console.error(
            "Failed to fetch achievements:",
            achievementsResponse.error
          );
        } else if (achievementsResponse.data) {
          setAchievements(achievementsResponse.data);
        }
      }
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const handleCreateNewExam = async () => {
    if (!profile) return;

    try {
      const response = await apiCall<ChatRoomResponse>(
        `/api/v1/chatrooms/?user_id=${profile.id}`,
        "POST",
        {
          chat_name: newExamName,
        }
      );

      if (response.error) {
        console.error("Failed to create new chat room:", response.error);
      } else if (response.data) {
        setShowNewExamDialog(false);
        router.push(`/chat/${profile.id}/${response.data.data.chat_id}`);
      }
    } catch (error) {
      console.error("Error creating new chat room:", error);
    }
  };

  const handleDelete = async () => {
    if (!profile || !deletingItem) return;

    setIsDeleting(true);
    setDeleteMessage("");

    try {
      const deleteId =
        "test_name" in deletingItem
          ? deletingItem.ctrm_id
          : deletingItem.chat_id;
      const response = await apiCall<{ message: string }>(
        `/api/v1/chatrooms/?user_id=${profile.id}&chat_id=${deleteId}`,
        "DELETE"
      );

      if (response.error) {
        console.error("Failed to delete item:", response.error);
        setDeleteMessage("삭제에 실패했습니다. 다시 시도해 주세요.");
      } else if (response.data) {
        setDeleteMessage(response.data.message);
        if ("test_name" in deletingItem) {
          setOngoingExams(
            ongoingExams.filter((exam) => exam.id !== deletingItem.id)
          );
        } else {
          setChatRooms(chatRooms.filter((room) => room.id !== deletingItem.id));
        }
      }
    } catch (error) {
      console.error("Error deleting item:", error);
      setDeleteMessage("삭제 중 오류가 발생했습니다. 다시 시도해 주세요.");
    } finally {
      setIsDeleting(false);
    }
  };

  const handleViewProfile = async () => {
    setIsLoadingProfileDetails(true);
    setShowProfileDialog(true);

    try {
      const profileResponse = await apiCall<UserProfile>(
        "/api/v1/accounts/profile/",
        "GET"
      );

      if (profileResponse.error) {
        console.error(
          "Failed to fetch profile details:",
          profileResponse.error
        );
      } else if (profileResponse.data) {
        setProfile(profileResponse.data);
      }
    } catch (error) {
      console.error("Error fetching profile details:", error);
    } finally {
      setIsLoadingProfileDetails(false);
    }
  };

  const handleEdit = (field: "username" | "email") => {
    setEditingField(field);
    setEditError("");
    setShowEditDialog(true);
  };

  const handleUpdateProfile = async (value: string) => {
    if (!profile) return;

    try {
      const response = await apiCall<any>(
        "/api/v1/accounts/profile/",
        "PATCH",
        {
          [editingField!]: value,
        }
      );

      if (response.error) {
        if (response.status === 400 && response.data) {
          setEditError(response.data[editingField!][0]);
        } else {
          setEditError("프로필 업데이트에 실패했습니다.");
        }
        // Keep the dialog open on error
        return;
      }

      // Update local profile state and close dialog only on success
      setProfile((prev) => (prev ? { ...prev, [editingField!]: value } : null));
      setShowEditDialog(false);
      setEditError("");
    } catch (error) {
      console.error("Error updating profile:", error);
      setEditError("프로필 업데이트 중 오류가 발생했습니다.");
      // Keep the dialog open on error
    }
  };

  const handleWithdrawal = async () => {
    setIsWithdrawing(true);
    setWithdrawalError("");

    try {
      const response = await apiCall<{ message: string }>(
        "/api/v1/accounts/withdrawal",
        "DELETE",
        {
          password: withdrawalPassword,
        }
      );

      if (response.error) {
        if (response.status === 400 && response.data) {
          setWithdrawalError(response.data.message);
        } else {
          setWithdrawalError("회원 탈퇴 중 오류가 발생했습니다.");
        }
      } else {
        // Successful withdrawal
        logout();
        router.push("/login");
      }
    } catch (error) {
      console.error("Error during withdrawal:", error);
      setWithdrawalError("회원 탈퇴 중 오류가 발생했습니다.");
    } finally {
      setIsWithdrawing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="container max-w-2xl mx-auto p-4 space-y-8">
        {/* Header Skeleton */}
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Skeleton className="h-12 w-12 rounded-full" />
            <Skeleton className="h-6 w-32" />
          </div>
          <div className="flex items-center gap-4">
            <Skeleton className="h-8 w-8 rounded-full" />
            <Skeleton className="h-8 w-8 rounded-full" />
            <Skeleton className="h-8 w-8 rounded-full" />
          </div>
        </header>

        {/* Achievements Section Skeleton */}
        <section className="space-y-4">
          <Skeleton className="h-8 w-40" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2].map((i) => (
              <Skeleton key={i} className="h-32 w-full rounded-lg" />
            ))}
          </div>
        </section>

        {/* Ongoing Exams Section Skeleton */}
        <section className="space-y-4">
          <Skeleton className="h-8 w-48" />
          <div className="space-y-4">
            <Skeleton className="h-24 w-full rounded-lg" />
          </div>
        </section>

        {/* Chat Rooms Section Skeleton */}
        <section className="space-y-4">
          <Skeleton className="h-8 w-48" />
          <div className="space-y-4">
            <Skeleton className="h-24 w-full rounded-lg" />
          </div>
        </section>

        {/* Generate New Plan Button Skeleton */}
        <Skeleton className="h-14 w-full rounded-full" />
      </div>
    );
  }

  return (
    <div className="container max-w-2xl mx-auto p-4 space-y-8">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Avatar className="h-12 w-12">
            <AvatarImage src="/placeholder.svg" alt="프로필" />
            <AvatarFallback className="text-xl">
              {profile?.username[0]}
            </AvatarFallback>
          </Avatar>
          <span className="text-lg font-medium">
            {profile?.username || "사용자 이름"}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <ModeToggle />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button>
                <Settings className="h-6 w-6" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>내 계정</DropdownMenuLabel>
              <DropdownMenuItem onSelect={handleViewProfile}>
                <User className="mr-2 h-4 w-4" />
                <span>프로필</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onSelect={() => setShowLogoutDialog(true)}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>로그아웃</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      {/* Achievements Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">나의 업적</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {isLoadingAchievements ? (
            [1, 2].map((i) => (
              <Skeleton key={i} className="h-32 w-full rounded-lg" />
            ))
          ) : achievements.length > 0 ? (
            achievements.map((achievement) => (
              <Card key={achievement.id} className="p-6">
                <p className="font-medium text-xl mb-2">
                  {achievement.test_name}
                </p>
                <p>
                  {new Date(achievement.created_at).toLocaleDateString()} 달성
                  완료
                </p>
              </Card>
            ))
          ) : (
            <Card className="w-full h-24 p-6 flex justify-center items-center col-span-2">
              아직 달성한 업적이 없습니다
            </Card>
          )}
        </div>
      </section>

      {/* Ongoing Exams Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">진행 중인 시험</h2>
        <div className="space-y-4">
          {isLoadingExams ? (
            <Skeleton className="h-24 w-full rounded-lg" />
          ) : ongoingExams.length > 0 ? (
            ongoingExams.map((exam) => (
              <Card
                key={exam.id}
                className="p-6 hover:border-primary dark:hover:border-white transition-colors cursor-pointer relative group"
              >
                <div
                  onClick={() => {
                    localStorage.setItem(
                      "selectedExamId",
                      `${profile?.id}:${exam.plan_id}`
                    );
                    router.push("/dashboard");
                  }}
                  className="flex justify-between items-start"
                >
                  <div>
                    <h3 className="font-medium">{exam.test_name}</h3>
                    <p className="mt-1">{exam.test_place}</p>
                  </div>
                  <span>{formatDate(exam.test_date)}</span>
                </div>
                <Popover>
                  <PopoverTrigger asChild>
                    <button className="absolute top-2 right-2 p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors opacity-0 group-hover:opacity-100">
                      <MoreHorizontal className="h-4 w-4" />
                    </button>
                  </PopoverTrigger>
                  <PopoverContent
                    className="w-auto p-0"
                    align="start"
                    side="right"
                  >
                    <button
                      onClick={() => {
                        setDeletingItem(exam);
                        setShowDeleteDialog(true);
                      }}
                      className="flex items-center px-4 py-2 text-sm text-red-600 hover:bg-red-100 hover:rounded-md w-full"
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      <span>삭제하기</span>
                    </button>
                  </PopoverContent>
                </Popover>
              </Card>
            ))
          ) : (
            <Card className="w-full h-24 p-6 flex justify-center items-center">
              진행 중인 시험이 없습니다
            </Card>
          )}
        </div>
      </section>

      {/* Chat Rooms Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">채팅 계속하기</h2>
        <div className="space-y-4">
          {isLoadingChatRooms ? (
            <Skeleton className="h-24 w-full rounded-lg" />
          ) : chatRooms.length > 0 ? (
            chatRooms
              .filter((room) => room.testplan === null)
              .map((room) => (
                <Card key={room.id} className="p-6 transition-colors">
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 className="font-medium">{room.chat_name}</h3>
                      <p className="text-sm text-gray-500">
                        생성일: {new Date(room.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        onClick={() =>
                          router.push(`/chat/${profile?.id}/${room.chat_id}`)
                        }
                        size="sm"
                      >
                        채팅 계속하기
                      </Button>
                      <Button
                        variant={"destructive"}
                        onClick={() => {
                          setDeletingItem(room);
                          setShowDeleteDialog(true);
                        }}
                        size="sm"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </Card>
              ))
          ) : (
            <Card className="w-full h-24 p-6 flex justify-center items-center">
              현재 활성화된 채팅이 없습니다
            </Card>
          )}
        </div>
      </section>

      {/* Generate New Plan Button */}
      <Button
        size="lg"
        className="w-full text-lg py-6 rounded-full"
        onClick={() => setShowNewExamDialog(true)}
      >
        + 새로운 시험 계획 생성하기
      </Button>

      {/* Logout Confirmation Dialog */}
      <AlertDialog open={showLogoutDialog} onOpenChange={setShowLogoutDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>로그아웃 하시겠습니까?</AlertDialogTitle>
            <AlertDialogDescription>
              학습 알림을 설정하셨다면 계속 받을 수 있습니다.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <AlertDialogAction onClick={handleLogout}>
              로그아웃
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* New Exam Plan Dialog */}
      <AlertDialog open={showNewExamDialog} onOpenChange={setShowNewExamDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>채팅방 이름을 적어주세요.</AlertDialogTitle>
            <AlertDialogDescription>
              <div className="mb-4">
                계획 생성 전 채팅 중단 시 채팅 계속하기 부분에 표시되는
                이름입니다.
              </div>
              <Input
                type="text"
                placeholder="채팅 이름"
                value={newExamName}
                onChange={(e) => setNewExamName(e.target.value)}
                className="mt-2"
              />
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleCreateNewExam}
              disabled={!newExamName.trim()}
              className={
                !newExamName.trim() ? "opacity-50 cursor-not-allowed" : ""
              }
            >
              확인
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {deletingItem && "test_name" in deletingItem
                ? "시험을 삭제하시겠습니까?"
                : "채팅방을 삭제하시겠습니까?"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              이 작업은 되돌릴 수 없습니다.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <AlertDialogAction
              className="hover:bg-destructive/80 bg-destructive"
              onClick={handleDelete}
            >
              삭제
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Profile Details Dialog */}
      <AlertDialog open={showProfileDialog} onOpenChange={setShowProfileDialog}>
        <AlertDialogContent className="max-w-md">
          <div className="flex flex-col items-center space-y-6">
            {/* Profile Avatar */}
            <div className="w-32 h-32 rounded-full bg-secondary flex items-center justify-center">
              <span className="text-4xl">
                {profile?.username?.[0]?.toUpperCase()}
              </span>
            </div>

            {/* Profile Information */}
            <div className="w-full space-y-4">
              {/* Username */}
              <div className="relative w-full">
                <div className="flex items-center justify-between">
                  <span className="text-xl">{profile?.username}</span>
                  <button
                    onClick={() => handleEdit("username")}
                    className="p-1 hover:bg-muted rounded-full transition-colors"
                  >
                    <PencilIcon className="w-4 h-4 text-muted-foreground" />
                  </button>
                </div>
              </div>

              {/* Email */}
              <div className="relative w-full">
                <div className="flex items-center justify-between">
                  <span className="text-xl">{profile?.email}</span>
                  <button
                    onClick={() => handleEdit("email")}
                    className="p-1 hover:bg-muted rounded-full transition-colors"
                  >
                    <PencilIcon className="w-4 h-4 text-muted-foreground" />
                  </button>
                </div>
              </div>
            </div>

            {/* Withdraw Button */}
            <Button
              variant="ghost"
              className="w-full flex justify-center text-muted-foreground"
              onClick={() => setShowWithdrawalDialog(true)}
            >
              회원 탈퇴하기
            </Button>

            {/* Close Button */}
            <Button
              className="w-full py-6 text-lg"
              onClick={() => setShowProfileDialog(false)}
            >
              닫기
            </Button>
          </div>
        </AlertDialogContent>
      </AlertDialog>

      {/* Withdrawal Confirmation Dialog */}
      <AlertDialog
        open={showWithdrawalDialog}
        onOpenChange={setShowWithdrawalDialog}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>회원 탈퇴</AlertDialogTitle>
            <AlertDialogDescription>
              정말로 탈퇴하시겠습니까? 이 작업은 되돌릴 수 없습니다.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="space-y-4">
            <Input
              type="password"
              placeholder="비밀번호를 입력해주세요"
              value={withdrawalPassword}
              onChange={(e) => setWithdrawalPassword(e.target.value)}
            />
            {withdrawalError && (
              <p className="text-sm text-destructive">{withdrawalError}</p>
            )}
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setShowWithdrawalDialog(false)}>
              취소
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleWithdrawal}
              disabled={isWithdrawing || !withdrawalPassword.trim()}
              className="bg-destructive hover:bg-destructive/90 text-destructive-foreground"
            >
              탈퇴하기
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Edit Dialog */}
      {showEditDialog && editingField && (
        <EditDialog
          isOpen={showEditDialog}
          onClose={() => {
            setShowEditDialog(false);
            setEditingField(null);
            setEditError("");
          }}
          fieldName={editingField}
          currentValue={profile?.[editingField] || ""}
          onSubmit={handleUpdateProfile}
          error={editError}
        />
      )}
    </div>
  );
}
