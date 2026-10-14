/** Normalize legacy [question, answer] and reviewed object FAQ entries without losing answers. */
export function normalizeFaq(items) {
  if (items == null) return [];
  if (!Array.isArray(items)) throw new TypeError('FAQ must be an array');
  return items.map((item, index) => {
    const question = Array.isArray(item) ? item[0] : item?.question;
    const answer = Array.isArray(item) ? item[1] : item?.answer;
    if (typeof question !== 'string' || !question.trim() || typeof answer !== 'string' || !answer.trim()) {
      throw new TypeError(`FAQ entry ${index + 1} requires a nonempty question and answer`);
    }
    return {question, answer};
  });
}
