import React from "react";
import EventList from "./eventlist.jsx";

export default function Root() {
  return (
    <>
      <h1>Entry Ninja</h1>
      <button onClick={selectDirectory}>Select Directory</button>
    </>
  );
}

async function selectDirectory() {
  const databaseDirectory = await window.electron.ipcRenderer.invoke(
    "select-directory",
    "export"
  );
  console.log(databaseDirectory);
}
