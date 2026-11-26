import { useCallback, useEffect, useReducer, useRef } from 'react';

/**
 * Open/pin state shared by the image dots and the parts list.
 * Hover opens a panel; leaving closes it after a short delay (so the pointer
 * can travel into the panel); click/tap pins it open until closed.
 */
const initial = { openId: null, pinned: false };

function reducer(state, action) {
  switch (action.type) {
    case 'show':
      return state.openId === action.id ? state : { openId: action.id, pinned: false };
    case 'hide':
      return state.pinned ? state : initial;
    case 'toggle':
      return state.openId === action.id && state.pinned ? initial : { openId: action.id, pinned: true };
    case 'close':
      return initial;
    default:
      return state;
  }
}

export default function useHotspots() {
  const [state, dispatch] = useReducer(reducer, initial);
  const timer = useRef(null);
  const cancel = useCallback(() => clearTimeout(timer.current), []);

  const show = useCallback((id) => { cancel(); dispatch({ type: 'show', id }); }, [cancel]);
  const hide = useCallback(() => {
    cancel();
    timer.current = setTimeout(() => dispatch({ type: 'hide' }), 220);
  }, [cancel]);
  const toggle = useCallback((id) => { cancel(); dispatch({ type: 'toggle', id }); }, [cancel]);
  const close = useCallback(() => { cancel(); dispatch({ type: 'close' }); }, [cancel]);

  useEffect(() => cancel, [cancel]);

  return { ...state, show, hide, toggle, close, keepOpen: cancel };
}
