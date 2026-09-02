import { useEffect, useRef } from "react";
import type { Provider } from "../types/vehicle";

declare global {
    interface Window {
        L: any;
    }
}

interface InteractiveMapProps {
    userLat: number;
    userLng: number;
    userLocationName?: string;
    providers: Provider[];
    primaryProviderId?: number;
}

export default function InteractiveMap({
    userLat,
    userLng,
    userLocationName = "Your Breakdown Location",
    providers = [],
    primaryProviderId,
}: InteractiveMapProps) {
    const mapContainerRef = useRef<HTMLDivElement>(null);
    const mapInstanceRef = useRef<any>(null);

    useEffect(() => {
        if (!mapContainerRef.current) return;

        // Use Leaflet if available on window
        const L = window.L;

        if (L) {
            // Clean up existing map instance if re-rendering
            if (mapInstanceRef.current) {
                mapInstanceRef.current.remove();
                mapInstanceRef.current = null;
            }

            // Ensure coordinates are valid floats
            const lat = Number(userLat) || 12.9345;
            const lng = Number(userLng) || 77.6265;

            const map = L.map(mapContainerRef.current, {
                center: [lat, lng],
                zoom: 13,
                zoomControl: true,
            });

            mapInstanceRef.current = map;

            // Add OpenStreetMap Tile Layer
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
                maxZoom: 18,
            }).addTo(map);

            // User Breakdown Location Pin (Red Icon)
            const userIcon = L.divIcon({
                className: "custom-leaflet-user-pin",
                html: `<div style="background:#ef4444; color:white; padding:6px 10px; border-radius:20px; font-weight:bold; font-size:12px; border:2px solid white; box-shadow:0 3px 8px rgba(0,0,0,0.4); white-space:nowrap;">🚨 Your Location</div>`,
                iconSize: [110, 30],
                iconAnchor: [55, 15],
            });

            L.marker([lat, lng], { icon: userIcon })
                .addTo(map)
                .bindPopup(`<b>🚨 Breakdown Location</b><br/>${userLocationName}`)
                .openPopup();

            // Bounds to auto-fit all markers
            const bounds = L.latLngBounds([[lat, lng]]);

            // Place Provider Pins
            providers.forEach((provider) => {
                const pLat = Number(provider.latitude) || (lat + (Math.random() - 0.5) * 0.04);
                const pLng = Number(provider.longitude) || (lng + (Math.random() - 0.5) * 0.04);
                const isPrimary = provider.id === primaryProviderId || provider === providers[0];

                const providerIcon = L.divIcon({
                    className: "custom-leaflet-provider-pin",
                    html: `<div style="background:${isPrimary ? '#10b981' : '#0284c7'}; color:white; padding:5px 9px; border-radius:16px; font-weight:bold; font-size:11px; border:2px solid white; box-shadow:0 3px 8px rgba(0,0,0,0.3); white-space:nowrap;">
                            ${isPrimary ? '⭐ Top Match' : '🛠️'} ${provider.name.split(' ')[0]} (${provider.distanceKm} km)
                           </div>`,
                    iconSize: [140, 26],
                    iconAnchor: [70, 13],
                });

                L.marker([pLat, pLng], { icon: providerIcon })
                    .addTo(map)
                    .bindPopup(
                        `<b>${provider.name}</b><br/>` +
                        `⭐ ${provider.rating.toFixed(1)} / 5.0 | 📍 ${provider.distanceKm} km<br/>` +
                        `Services: ${provider.services.join(', ')}`
                    );

                bounds.extend([pLat, pLng]);

                // Draw connecting line to top match
                if (isPrimary) {
                    L.polyline([[lat, lng], [pLat, pLng]], {
                        color: '#10b981',
                        weight: 4,
                        dashArray: '8, 8',
                        opacity: 0.8,
                    }).addTo(map);
                }
            });

            // Adjust zoom to include user & providers
            if (providers.length > 0) {
                map.fitBounds(bounds, { padding: [40, 40] });
            }
        }

        return () => {
            if (mapInstanceRef.current) {
                mapInstanceRef.current.remove();
                mapInstanceRef.current = null;
            }
        };
    }, [userLat, userLng, providers, primaryProviderId]);

    return (
        <div className="interactive-map-wrapper">
            <div ref={mapContainerRef} className="leaflet-map-canvas" style={{ width: "100%", height: "260px", borderRadius: "12px", zIndex: 1 }} />
        </div>
    );
}
