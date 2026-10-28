import { useEffect, useState } from "react";

type Route = { name: "home" } | { name: "room"; roomId: string };

function parse(path: string): Route {
  const m = path.match(/^\/r\/([A-Za-z0-9_-]{22})\/?$/);
  return m?.[1] ? { name: "room", roomId: m[1] } : { name: "home" };
}

export function navigate(path: string) {
  history.pushState(null, "", path);
  dispatchEvent(new PopStateEvent("popstate"));
}

export function useRoute(): Route {
  const [route, setRoute] = useState(() => parse(location.pathname));
  useEffect(() => {
    const onPop = () => setRoute(parse(location.pathname));
    addEventListener("popstate", onPop);
    return () => removeEventListener("popstate", onPop);
  }, []);
  return route;
}
