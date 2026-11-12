package fr.citadelle.messages;

import org.bukkit.configuration.ConfigurationSection;

import java.time.DateTimeException;
import java.time.ZoneId;
import java.util.List;

/** Immutable snapshot of the "faille" config section. */
record RiftConfig(boolean enabled, String world, boolean auto, ZoneId zone, List<String> times, int minPlayers,
                  int minDistance, int maxDistance, int warmupSeconds, int maxDurationSeconds, int captureSeconds,
                  double radius, int waveIntervalSeconds, int maxMobs, List<String> rewardCommands,
                  List<String> participationCommands,
                  int chestProtectionSeconds, int chestLifetimeSeconds, List<String> loot) {

    private static final List<String> DEFAULT_TIMES = List.of("15:00", "18:00", "21:00");
    private static final List<String> DEFAULT_REWARDS = List.of("eco give {player} 5000");
    private static final List<String> DEFAULT_PARTICIPATION = List.of("eco give {player} 750");
    private static final List<String> DEFAULT_LOOT = List.of(
            "RELIC 1 100", "RELIC 1 25", "DIAMOND 8-16 100", "NETHERITE_INGOT 1-2 45", "NETHERITE_SCRAP 2-4 70",
            "ENCHANTED_GOLDEN_APPLE 1-2 40", "GOLDEN_APPLE 6-12 100", "TOTEM_OF_UNDYING 1-2 50",
            "ENCHANTED_BOOK:mending 1 50", "ENCHANTED_BOOK:sharpness 1 40", "ENCHANTED_BOOK:protection 1 40",
            "ENCHANTED_BOOK:efficiency 1 30", "ENCHANTED_BOOK:unbreaking 1 30", "EMERALD_BLOCK 3-6 80",
            "EXPERIENCE_BOTTLE 24-48 100", "ENDER_PEARL 8-16 90", "SHULKER_BOX 1 25", "ELYTRA 1 6",
            "CHRONON 10-20 100");

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
                listOr(s, "participation-commands", DEFAULT_PARTICIPATION),
                Math.max(0, s.getInt("chest-protection-seconds", 60)),
                Math.max(30, s.getInt("chest-lifetime-seconds", 300)),
                listOr(s, "loot", DEFAULT_LOOT));
    }

    private static List<String> listOr(ConfigurationSection s, String key, List<String> fallback) {
        return s.isList(key) ? List.copyOf(s.getStringList(key)) : fallback;
    }
}
