import { useEffect, useState } from "react";
import { MapContainer, TileLayer } from "react-leaflet";

function App() {
  const [apiStatus, setApiStatus] = useState<string>("Checking backend...");

  useEffect(() => {
    fetch("http://localhost:8000/api/health")
      .then((res) => res.json())
      .then((data) => setApiStatus(data.message))
      .catch(() => setApiStatus("Backend disconnected."));
  }, []);

  return (
    <div className="flex h-screen w-screen flex-col md:flex-row font-sans">
      {/* SIDEBAR */}
      <div className="w-full md:w-96 bg-gray-900 text-white p-6 flex flex-col shadow-2xl z-10">
        <h1 className="text-3xl font-bold mb-2 text-red-500">NAHvigate</h1>
        <p className="text-gray-400 text-sm mb-6">
          Are you sure you wanna take this route?
        </p>

        <div className="bg-gray-800 p-4 rounded-lg mb-4 text-sm border border-gray-700">
          <span className="font-semibold text-gray-300">API Status: </span>
          <span
            className={
              apiStatus.includes("terribly") ? "text-green-400" : "text-red-400"
            }
          >
            {apiStatus}
          </span>
        </div>

        <div className="mt-auto pt-4 border-t border-gray-800">
          <p className="text-xs text-gray-500 text-center">Coming soon</p>
        </div>
      </div>

      {/* MAP AREA */}
      <div className="flex-1 relative z-0">
        <MapContainer
          center={[43.651, -79.347]}
          zoom={10}
          className="h-full w-full"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
        </MapContainer>
      </div>
    </div>
  );
}

export default App;
