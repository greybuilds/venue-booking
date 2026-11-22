# Slot Drift

A generative piece for the Roomly sign-in pages.

Booking is a negotiation over time. Requests arrive at random, each wanting a room and a stretch of hours, and most land cleanly. When two want the same slot, the system does not refuse either: the late one flares orange, then slides along the timetable until it finds the nearest free place and settles. Nothing is scripted. Every run is a different afternoon, and a seed always replays the same one.

The algorithm is a small simulation. A grid of rooms by half hours holds occupancy. Requests spawn from a seeded stream, a clash is detected by overlap, and the resolver searches outward by distance for a free slot. Motion is eased interpolation, so blocks drift and settle instead of snapping. Settled blocks age and release their slots, which keeps the timetable breathing without ever filling up.

The palette is the site's own: white, ink, one orange. Orange only ever means a clash in progress, the same rule the interface follows for action and selection. The craft is in the restraint: hairline grid, few blocks, long calm intervals between conflicts.

## Gates

A band between the rules sentence and the steps. Requests stream left to right as ink dots through four gates, one for each rule: hours, clashes, length, weekly limit. A dot that arrives outside a gate's opening turns orange and steers into it, then goes back to ink. Orange is again only the correction.

## Dial

A day drawn as a circle behind the closing line. Each ring is a room, each arc a booking. One orange hand sweeps round as the current time, and any booking it touches flares for a moment. Bookings come and go from a seeded stream.
