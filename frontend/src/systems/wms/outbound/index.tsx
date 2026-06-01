import { Route, Routes } from "react-router-dom";

import SalesOrderDetailPage from "./SalesOrderDetailPage";
import SalesOrdersPage from "./SalesOrdersPage";

export default function OutboundRoutes() {
  return (
    <Routes>
      <Route index element={<SalesOrdersPage />} />
      <Route path=":soId" element={<SalesOrderDetailPage />} />
    </Routes>
  );
}
