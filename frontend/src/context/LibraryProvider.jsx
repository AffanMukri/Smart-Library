import { LibraryContext } from "./library-context";
import { useLibraryDashboard } from "../hooks/useLibraryDashboard";

export default function LibraryProvider({ children }) {
  const library = useLibraryDashboard(1000);
  return <LibraryContext.Provider value={library}>{children}</LibraryContext.Provider>;
}

