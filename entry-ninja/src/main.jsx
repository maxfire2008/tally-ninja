import * as React from "react";
import * as ReactDOM from "react-dom/client";
// import {
//   createBrowserRouter,
//   RouterProvider,
// } from "react-router-dom";
import "./index.css";

import Root from "./routes/root.jsx";

// const router = createBrowserRouter([
//   {
//     path: "/main_window",
//     element: <Root />,
//   },
// ]);

ReactDOM.createRoot(document.getElementById("root")).render(
  // <React.StrictMode>
  //   <RouterProvider router={router} />
  // </React.StrictMode>
  <Root />
);
