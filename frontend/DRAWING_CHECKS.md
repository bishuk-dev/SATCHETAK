# Rectangle selection checks

Run `npm run test:e2e` from `frontend` for automated Chrome checks of drawing, cancellation, touch, zoom coordinates, mobile layout, and both purchase reports. Chrome and the repository `.venv` with backend dependencies must be installed. Tests start a frontend on port 5174 and an isolated backend on port 8001, with data in `frontend/.test-api-data`. Map tiles are mocked. The location-payload test mocks API responses; the purchase-report test runs the real demo API. No live satellite analysis is tested.

Run the frontend and backend, select **Demo - offline evidence**, and open the map.

1. Choose **Draw rectangle**, drag diagonally, and release. The selected outline and all four coordinate inputs should match the new rectangle. Repeat dragging in the opposite direction.
2. Submit immediately after drawing. Browser number validation must accept full-precision coordinates; the request should produce demo evidence for the selected location.
3. Start another rectangle and press Escape before releasing. The previous area should remain selected. Start drawing again to verify capture and map controls recovered.
4. Release a drag outside the map. Selection should finish at the map edge and ordinary panning should work afterward.
5. Click without dragging, or move fewer than four pixels along either axis. The selected area should remain unchanged.
6. Cancel using the drawing button, switch away from the browser during a drag, or interrupt a touch gesture. Drawing should end without replacing the selected area.
7. On a touch device, drag a rectangle with one finger. Pinch and rotate gestures should not move the map while drawing; navigation should work after drawing ends.
8. Draw a new area after results appear. Old results and observation selections should disappear. While a request is running, coordinate editing and drawing should be disabled.
9. Enter reversed or out-of-range bounds. Submission should be rejected without a request. Correct the values and verify submission works again.

These checks require a browser with WebGL. Build and lint checks alone do not verify pointer capture or touch behavior. Demo results are synthetic and do not establish real-world vegetation change.
