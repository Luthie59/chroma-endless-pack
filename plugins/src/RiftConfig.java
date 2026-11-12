package fr.citadelle.messages;

import org.bukkit.configuration.ConfigurationSection;

import java.time.DateTimeException;
import java.time.ZoneId;
import java.util.List;

/** Immutable snapshot of the "faille" config section. */
record RiftConfig(boolean enabled, String world, boolean auto, ZoneId zone, List<String> times, int minPlayers,
                  int minDistance, int maxDistance, int warmupSeconds, int maxDurationSeconds, int captureSeconds,
                  double radius, int waveIntervalSeconds, int maxMobs, List<String> rewardCommands,
                  int chestProtectionSeconds, int chestLifetimeSeconds, List<String> loot) {

    private static final List<String> DEFAULT_TIMES = List.of("15:00", "18:00", "21:00");
    private static final List<String> DEFAULT_REWARDS = List.of("eco give {player} 2500");
    private static final List<String> DEFAULT_LOOT = List.of(
            "DIAMOND 2-5 100", "GOLDEN_APPLE 2-4 100", "ENCHANTED_GOLDEN_APPLE 1 15", "NETHERITE_SCRAP 1-2 40",
            "EMERALD 8-16 80", "EXPERIENCE_BOTTLE 8-16 80", "ENDER_PEARL 4-8 70", "TOTEM_OF_UNDYING 1 20",
            "CHRONON 3-6 100");

    static RiftConfig load(ConfigurationSection s) {
        ZoneId zone;
        try {
            zone = ZoneId.of(s.getString("timezone", "Europe/Paris"));
        } catch (DateTimeException e) {
            zone = ZoneId.of("Europe/Paris");
        }
        int min = Math.max(150, s.getInt("min-distance", 600));
        int max = Math.max(min + 50, s.getInt("max-distance", 1800));
        return new RiftConfig(
                s.getBoolean("enabled", true),
                s.getString("world", "world"),
                s.getBoolean("auto", true),
                zone,
                listOr(s, "times", DEFAULT_TIMES),
                Math.max(0, s.getInt("min-players", 2)),
                min, max,
                Math.max(10, s.getInt("warmup-seconds", 300)),
                Math.max(60, s.getInt("max-duration-seconds", 1200)),
                Math.max(10, s.getInt("capture-seconds", 180)),
                Math.max(2.0, s.getDouble("radius", 6.0)),
                Math.max(10, s.getInt("wave-interval-seconds", 45)),
                Math.max(0, s.getInt("max-mobs", 18)),
                listOr(s, "reward-commands", DEFAULT_REWARDS),
                Math.max(0, s.getInt("chest-protection-seconds", 60)),
                Math.max(30, s.getInt("chest-lifetime-seconds", 300)),
                listOr(s, "loot", DEFAULT_LOOT));
    }

    private static List<String> listOr(ConfigurationSection s, String key, List<String> fallback) {
        return s.isList(key) ? List.copyOf(s.getStringList(key)) : fallback;
    }
}
