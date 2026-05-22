import { Route, Routes } from "react-router-dom";

import PurchaseOrderDetailPage from "./PurchaseOrderDetailPage";
import PurchaseOrdersPage from "./PurchaseOrdersPage";

export default function InboundRoutes() {
  return (
    <Routes>
      <Route index element={<PurchaseOrdersPage />} />
      <Route path=":poId" element={<PurchaseOrderDetailPage />} />
    </Routes>
  );
}
