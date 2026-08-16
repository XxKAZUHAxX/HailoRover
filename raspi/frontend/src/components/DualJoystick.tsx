import type React from "react";
import type { JoystickPosition } from "../types";

interface JoystickProps {
  label: string;
  axisLabel: string;
  joystickRef: React.RefObject<HTMLDivElement>;
  position: JoystickPosition;
  active: boolean;
}

function Joystick({ label, axisLabel, joystickRef, position, active }: JoystickProps) {
  const knobX = position.x * 30;
  const knobY = -position.y * 30;

  return (
    <div className="flex flex-col items-center gap-2">
      <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">
        {label}
      </span>
      <div
        ref={joystickRef}
        className={`relative w-28 h-28 rounded-full border-2 cursor-pointer touch-none select-none transition-colors ${
          active
            ? "border-accent bg-surface-overlay"
            : "border-surface-overlay bg-surface-raised hover:border-gray-600"
        }`}
        style={{ touchAction: "none" }}
      >
        {/* Crosshair guides */}
        <div className="absolute top-1/2 left-0 right-0 h-px bg-gray-700" />
        <div className="absolute top-0 bottom-0 left-1/2 w-px bg-gray-700" />

        {/* Knob */}
        <div
          className="absolute w-8 h-8 rounded-full bg-accent shadow-lg shadow-accent/30 transition-transform duration-75"
          style={{
            left: `calc(50% - 16px + ${knobX}px)`,
            top: `calc(50% - 16px + ${knobY}px)`,
          }}
        />

        {/* Axis label */}
        <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-[10px] font-mono text-gray-600 whitespace-nowrap">
          {axisLabel}
        </span>
      </div>
    </div>
  );
}

interface DualJoystickProps {
  leftRef: React.RefObject<HTMLDivElement>;
  rightRef: React.RefObject<HTMLDivElement>;
  leftPos: JoystickPosition;
  rightPos: JoystickPosition;
  leftActive: boolean;
  rightActive: boolean;
}

export function DualJoystick({
  leftRef,
  rightRef,
  leftPos,
  rightPos,
  leftActive,
  rightActive,
}: DualJoystickProps) {
  return (
    <div className="flex items-center justify-center gap-8 p-4">
      <Joystick
        label="Forward / Rev"
        axisLabel="↑↓ Speed"
        joystickRef={leftRef}
        position={leftPos}
        active={leftActive}
      />
      <Joystick
        label="Left / Right"
        axisLabel="←→ Turn"
        joystickRef={rightRef}
        position={rightPos}
        active={rightActive}
      />
    </div>
  );
}
