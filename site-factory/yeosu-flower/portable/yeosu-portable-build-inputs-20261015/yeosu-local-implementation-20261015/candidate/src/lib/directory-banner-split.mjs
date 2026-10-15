/** Choose one insertion point among actual cards, never among collapsed details.
 * @param {number[]} cardCounts Counts in the existing district order.
 * @param {boolean} requested Existing page-level banner eligibility.
 */
export function planDirectoryBannerSplit(cardCounts, requested = true) {
  if (!Array.isArray(cardCounts) || cardCounts.some(n => !Number.isSafeInteger(n) || n < 0)) {
    throw new TypeError('Directory card counts must be nonnegative safe integers');
  }
  const totalCards = cardCounts.reduce((sum, count) => sum + count, 0);
  if (!Number.isSafeInteger(totalCards)) throw new RangeError('Directory card total exceeds safe integer range');
  if (requested && totalCards < 2) {
    throw new RangeError('Requested regional banners require at least two actual cards');
  }
  const enabled = requested;
  const splitAfter = enabled ? Math.ceil(totalCards / 2) : null;
  let offset = 0;
  let districtIndex = -1;
  let itemIndex = -1;
  if (enabled) {
    for (let index = 0; index < cardCounts.length; index += 1) {
      const count = cardCounts[index];
      if (splitAfter > offset && splitAfter <= offset + count) {
        districtIndex = index;
        itemIndex = splitAfter - offset;
        break;
      }
      offset += count;
    }
  }
  return {enabled, totalCards, splitAfter, districtIndex, itemIndex};
}
