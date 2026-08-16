import { useRef, useState, useCallback, useEffect } from "react";
import type { JoystickPosition } from "../types";

interface UseJoystickOptions {
  onChange: (id: string, pos: JoystickPosition) => void;
  onRelease: (id: string) => void;
}

interface JoystickState {
  id: string;
  position: JoystickPosition;
  active: boolean;
}

/**
 * Handles touch + mouse input for a dual joystick setup.
 * Returns refs to attach to the two joystick container elements.
 */
export function useJoystick({ onChange, onRelease }: UseJoystickOptions) {
  const [leftState, setLeftState] = useState<JoystickState>({
    id: "forward",
    position: { x: 0, y: 0 },
    active: false,
  });
  const [rightState, setRightState] = useState<JoystickState>({
    id: "turn",
    position: { x: 0, y: 0 },
    active: false,
  });

  const leftRef = useRef<HTMLDivElement>(null);
  const rightRef = useRef<HTMLDivElement>(null);

  const sendMotorCommand = useCallback(
    (forward: JoystickPosition, turn: JoystickPosition) => {
      // Forward joystick: Y-axis → forward/reverse
      // Turn joystick: X-axis → left/right
      fetch("/api/control/joystick", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          forward: -forward.y, // Invert Y: up = positive = forward
          turn: turn.x,       // X: positive = right
        }),
      }).catch(() => {
        // Motor control may be disabled
      });
    },
    []
  );

  const handleJoystickMove = useCallback(
    (id: string, element: HTMLDivElement, clientX: number, clientY: number) => {
      const rect = element.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      const maxRadius = rect.width / 2 - 16;

      let dx = clientX - centerX;
      let dy = clientY - centerY;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist > maxRadius) {
        dx = (dx / dist) * maxRadius;
        dy = (dy / dist) * maxRadius;
      }

      const pos: JoystickPosition = {
        x: dx / maxRadius,
        y: -dy / maxRadius,
      };

      if (id === "forward") {
        setLeftState({ id, position: pos, active: true });
        onChange(id, pos);
        sendMotorCommand(pos, rightState.position);
      } else {
        setRightState({ id, position: pos, active: true });
        onChange(id, pos);
        sendMotorCommand(leftState.position, pos);
      }
    },
    [onChange, sendMotorCommand, leftState.position, rightState.position]
  );

  const handleRelease = useCallback(
    (id: string) => {
      const zero = { x: 0, y: 0 };
      if (id === "forward") {
        setLeftState({ id, position: zero, active: false });
        sendMotorCommand(zero, rightState.position);
      } else {
        setRightState({ id, position: zero, active: false });
        sendMotorCommand(leftState.position, zero);
      }
      onRelease(id);
    },
    [onRelease, sendMotorCommand, leftState.position, rightState.position]
  );

  // Attach event listeners
  useEffect(() => {
    const attachEvents = (
      ref: React.RefObject<HTMLDivElement>,
      id: string
    ) => {
      const el = ref.current;
      if (!el) return;

      const onPointerDown = (e: PointerEvent) => {
        el.setPointerCapture(e.pointerId);
        handleJoystickMove(id, el, e.clientX, e.clientY);
      };
      const onPointerMove = (e: PointerEvent) => {
        if (el.hasPointerCapture(e.pointerId)) {
          handleJoystickMove(id, el, e.clientX, e.clientY);
        }
      };
      const onPointerUp = (e: PointerEvent) => {
        el.releasePointerCapture(e.pointerId);
        handleRelease(id);
      };

      el.addEventListener("pointerdown", onPointerDown);
      el.addEventListener("pointermove", onPointerMove);
      el.addEventListener("pointerup", onPointerUp);
      el.addEventListener("pointercancel", onPointerUp);

      return () => {
        el.removeEventListener("pointerdown", onPointerDown);
        el.removeEventListener("pointermove", onPointerMove);
        el.removeEventListener("pointerup", onPointerUp);
        el.removeEventListener("pointercancel", onPointerUp);
      };
    };

    const cleanupLeft = attachEvents(leftRef, "forward");
    const cleanupRight = attachEvents(rightRef, "turn");

    return () => {
      cleanupLeft?.();
      cleanupRight?.();
    };
  }, [handleJoystickMove, handleRelease]);

  return { leftRef, rightRef, leftState, rightState };
}
