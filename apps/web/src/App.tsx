import { Home } from "./pages/Home.tsx";
import { RoomPage } from "./pages/RoomPage.tsx";
import { useRoute } from "./router.ts";

export function App() {
  const route = useRoute();
  return (
    <div className="mx-auto flex h-full max-w-lg flex-col">
      {route.name === "room" ? <RoomPage key={route.roomId} roomId={route.roomId} /> : <Home />}
    </div>
  );
}
