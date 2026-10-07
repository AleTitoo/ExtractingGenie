function allowOfflineRequest(destination, origin) {
  try {
    const parsed = new URL(destination);
    return parsed.origin === new URL(origin).origin || ['blob:', 'data:'].includes(parsed.protocol);
  } catch { return false; }
}
module.exports = { allowOfflineRequest };
