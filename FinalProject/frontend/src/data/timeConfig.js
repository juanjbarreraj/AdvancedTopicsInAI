export const TIME_SLOTS = [
  {
    label: "00:00-08:00",
    displayLabel: "12:00 AM - 8:00 AM",
    name: "Sleep",
    startMinutes: 0,
    endMinutes: 8 * 60,
  },
  {
    label: "08:00-09:30",
    displayLabel: "8:00 AM - 9:30 AM",
    name: "Morning Slot",
    startMinutes: 8 * 60,
    endMinutes: 9 * 60 + 30,
  },
  {
    label: "09:40-11:10",
    displayLabel: "9:40 AM - 11:10 AM",
    name: "Class / Activity",
    startMinutes: 9 * 60 + 40,
    endMinutes: 11 * 60 + 10,
  },
  {
    label: "11:20-12:50",
    displayLabel: "11:20 AM - 12:50 PM",
    name: "Class / Activity",
    startMinutes: 11 * 60 + 20,
    endMinutes: 12 * 60 + 50,
  },
  {
    label: "13:00-14:30",
    displayLabel: "1:00 PM - 2:30 PM",
    name: "Afternoon Slot",
    startMinutes: 13 * 60,
    endMinutes: 14 * 60 + 30,
  },
  {
    label: "15:00-15:30",
    displayLabel: "3:00 PM - 3:30 PM",
    name: "Track / Practice Transition",
    startMinutes: 15 * 60,
    endMinutes: 15 * 60 + 30,
  },
  {
    label: "16:00-17:30",
    displayLabel: "4:00 PM - 5:30 PM",
    name: "Practice / Activity",
    startMinutes: 16 * 60,
    endMinutes: 17 * 60 + 30,
  },
  {
    label: "18:00-21:00",
    displayLabel: "6:00 PM - 9:00 PM",
    name: "Evening",
    startMinutes: 18 * 60,
    endMinutes: 21 * 60,
  },
  {
    label: "21:00-00:00",
    displayLabel: "9:00 PM - 12:00 AM",
    name: "Free Time",
    startMinutes: 21 * 60,
    endMinutes: 24 * 60,
  },
];

export const SIMULATION_START_MINUTES = 8 * 60; // Starts at 8:00 AM for demo
export const SIMULATION_END_MINUTES = 24 * 60; // Midnight
export const SIMULATION_SPEED = 5; // 1 real second = 5 simulated minutes

export function formatMinutesToTime(totalMinutes) {
  const normalizedMinutes = totalMinutes % (24 * 60);

  const hours24 = Math.floor(normalizedMinutes / 60);
  const minutes = normalizedMinutes % 60;

  const suffix = hours24 >= 12 ? "PM" : "AM";
  let hours12 = hours24 % 12;

  if (hours12 === 0) {
    hours12 = 12;
  }

  return `${hours12}:${String(minutes).padStart(2, "0")} ${suffix}`;
}

export function getCurrentTimeSlotLabel(totalMinutes) {
  const normalizedMinutes = totalMinutes % (24 * 60);

  for (let i = 0; i < TIME_SLOTS.length; i++) {
    const currentSlot = TIME_SLOTS[i];
    const nextSlot = TIME_SLOTS[i + 1];

    const slotStart = currentSlot.startMinutes;
    const slotEnd = nextSlot ? nextSlot.startMinutes : currentSlot.endMinutes;

    if (normalizedMinutes >= slotStart && normalizedMinutes < slotEnd) {
      return currentSlot.label;
    }
  }

  return TIME_SLOTS[0].label;
}

export function getNextTimeSlotLabel(currentSlotLabel) {
  const currentIndex = TIME_SLOTS.findIndex(
    (slot) => slot.label === currentSlotLabel
  );

  if (currentIndex === -1) {
    return TIME_SLOTS[0].label;
  }

  const nextSlot = TIME_SLOTS[(currentIndex + 1) % TIME_SLOTS.length];

  return nextSlot.label;
}

export function getTimeSlotName(slotLabel) {
  const slot = TIME_SLOTS.find((item) => item.label === slotLabel);
  return slot ? slot.name : slotLabel;
}