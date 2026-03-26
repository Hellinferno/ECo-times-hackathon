import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./Dashboard";
import OpportunityDetail from "./OpportunityDetail";
import StockDetail from "./StockDetail";
import History from "./History";
import Watchlist from "./Watchlist";
import Alerts from "./Alerts";
import Settings from "./Settings";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/opportunity/:id" element={<OpportunityDetail />} />
          <Route path="/stock/:symbol" element={<StockDetail />} />
          <Route path="/history" element={<History />} />
          <Route path="/watchlist" element={<Watchlist />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
