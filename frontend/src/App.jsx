import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/home';
import Analysis from './pages/analysis';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/analysis/:gitname" element={<Analysis />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
