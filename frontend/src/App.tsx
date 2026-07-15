import { useState, useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Polyline,
  useMapEvents,
  GeoJSON,
} from "react-leaflet";
import L from "leaflet";

import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
});

function MapClickHandler({
  onMapClick,
}: {
  onMapClick: (lat: number, lng: number) => void;
}) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

function App() {
  const [boundary, setBoundary] = useState<any>(null);
  const [startPoint, setStartPoint] = useState<[number, number] | null>(null);
  const [endPoint, setEndPoint] = useState<[number, number] | null>(null);
  const [normalRoute, setNormalRoute] = useState<[number, number][]>([]);
  const [nahRoute, setNahRoute] = useState<[number, number][]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetch("http://localhost:8000/api/boundary")
      .then((res) => res.json())
      .then((data) => {
        if (!data.error) {
          setBoundary(data);
        }
      })
      .catch((err) => console.error("Failed to load boundary:", err));
  }, []);

  const handleMapClick = (lat: number, lng: number) => {
    if (!startPoint) {
      setStartPoint([lat, lng]);
    } else if (!endPoint) {
      setEndPoint([lat, lng]);
    } else {
      setStartPoint([lat, lng]);
      setEndPoint(null);
      setNormalRoute([]);
      setNahRoute([]);
    }
  };

  const generateAwfulRoute = async () => {
    if (!startPoint || !endPoint) return;
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/route", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          start_lat: startPoint[0],
          start_lon: startPoint[1],
          end_lat: endPoint[0],
          end_lon: endPoint[1],
        }),
      });
      const data = await response.json();
      setNormalRoute(data.normal_route);
      setNahRoute(data.nah_route);
    } catch (error) {
      console.error("Failed to fetch route:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen flex-col md:flex-row font-sans">
      <div className="w-full md:w-96 bg-gray-900 text-white p-6 flex flex-col shadow-2xl z-10">
        <h1 className="text-4xl font-black mb-2 text-red-500 tracking-tight">
          NAHvigate
        </h1>
        <p className="text-gray-400 text-sm mb-8">
          Are you sure you wanna take this route?
        </p>

        <div className="space-y-4 mb-8">
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">
              1. Origin
            </p>
            <p className="font-mono text-sm text-green-400">
              {startPoint
                ? `${startPoint[0].toFixed(4)}, ${startPoint[1].toFixed(4)}`
                : "Click map to set"}
            </p>
          </div>
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">
              2. Destination
            </p>
            <p className="font-mono text-sm text-red-400">
              {endPoint
                ? `${endPoint[0].toFixed(4)}, ${endPoint[1].toFixed(4)}`
                : "Click map to set"}
            </p>
          </div>
        </div>

        <button
          onClick={generateAwfulRoute}
          disabled={!startPoint || !endPoint || isLoading}
          className="bg-red-600 hover:bg-red-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-bold py-3 px-4 rounded-lg transition-colors"
        >
          {isLoading ? "Avoiding common sense..." : "Generate NAH Route"}
        </button>

        {nahRoute.length > 0 && (
          <div className="mt-8 space-y-2">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
              <span className="text-sm">Boring efficient route</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-500 rounded-full"></div>
              <span className="text-sm font-bold">Chaos route</span>
            </div>
          </div>
        )}

        <div className="mt-auto pt-4 border-t border-gray-800">
          <p className="text-xs text-gray-500 text-center">Coming soon</p>
        </div>
      </div>

      <div className="flex-1 relative z-0">
        <MapContainer
          center={[43.651, -79.347]}
          zoom={10}
          className="h-full w-full"
        >
          <TileLayer
            attribution="&copy; OpenStreetMap"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {boundary && (
            <GeoJSON
              data={boundary}
              style={{
                color: "#6b7280",
                weight: 2,
                dashArray: "5, 5",
                fillOpacity: 0.05,
              }}
            />
          )}

          <MapClickHandler onMapClick={handleMapClick} />

          {startPoint && <Marker position={startPoint} />}
          {endPoint && <Marker position={endPoint} />}

          {normalRoute.length > 0 && (
            <Polyline
              positions={normalRoute}
              color="#3b82f6"
              weight={5}
              opacity={0.7}
            />
          )}

          {nahRoute.length > 0 && (
            <Polyline
              positions={nahRoute}
              color="#ef4444"
              weight={6}
              opacity={0.9}
            />
          )}
        </MapContainer>
      </div>
    </div>
  );
}

export default App;
