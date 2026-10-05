export function occupancyMatrix(entities, occupancy, day, periodCount) {
  return entities.map((entity) =>
    Array.from({ length: periodCount }, (_, p) =>
      occupancy
        .filter(
          (x) =>
            x.index === entity.index && x.day === day && x.period === p + 1,
        )
        .reduce((sum, x) => sum + x.count, 0),
    ),
  );
}
export function hypotheticalCollision(assignment) {
  return Array.from({ length: assignment.duration }, (_, i) => ({
    index: assignment.faculty,
    day: assignment.day,
    period: assignment.start + i,
    count: 2,
  }));
}
