import { Route, Routes } from "react-router-dom";

import PlanningPage from "./PlanningPage";

export default function PlanningRoutes() {
  return (
    <Routes>
      <Route path="/" element={<PlanningPage />} />
    </Routes>
  );
}
