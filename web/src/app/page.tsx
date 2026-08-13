import { Chat } from "@/components/chat/chat";
import { SiteHeader } from "@/components/site-header";

export default function HomePage() {
  return (
    <div className="flex h-dvh flex-col">
      <SiteHeader />
      <Chat />
    </div>
  );
}
