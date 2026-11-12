package fr.citadelle.messages;

import me.clip.placeholderapi.expansion.PlaceholderExpansion;
import org.bukkit.Location;
import org.bukkit.OfflinePlayer;
import org.bukkit.entity.Player;

/**
 * PlaceholderAPI expansion "citadelle" (loaded only when PlaceholderAPI is present):
 * %citadelle_faille_etat%, _coords, _prochaine, _controle, _distance and %citadelle_chronons%.
 */
final class CitadelleExpansion extends PlaceholderExpansion {

    private final CitadelleMessages plugin;
    private final TimeRift rift;
    private final Chronon chronon;

    CitadelleExpansion(CitadelleMessages plugin, TimeRift rift, Chronon chronon) {
        this.plugin = plugin;
        this.rift = rift;
        this.chronon = chronon;
    }

    @Override public String getIdentifier() { return "citadelle"; }
    @Override public String getAuthor() { return "La Citadelle"; }
    @Override public String getVersion() { return plugin.getDescription().getVersion(); }
    @Override public boolean persist() { return true; }

    @Override
    public String onRequest(OfflinePlayer player, String params) {
        Location c = rift.center();
        return switch (params.toLowerCase(java.util.Locale.ROOT)) {
            case "faille_etat" -> switch (rift.phase()) {
                case WARMUP -> "§eOuverture dans " + fmt(rift.countdown());
                case ACTIVE -> "§a§lOuverte !";
                default -> "§cFermée";
            };
            case "faille_coords" -> c == null || rift.phase() == TimeRift.Phase.IDLE ? "§8—" : "§fX " + c.getBlockX() + " §7/ §fZ " + c.getBlockZ();
            case "faille_prochaine" -> {
                String next = rift.nextTime();
                yield next == null ? "§8—" : "§e" + next;
            }
            case "faille_controle" -> rift.phase() != TimeRift.Phase.ACTIVE ? "§8—" : rift.holderName() == null ? "§7Personne" : "§b" + rift.holderName();
            case "faille_distance" -> {
                if (c == null || rift.phase() == TimeRift.Phase.IDLE || !(player instanceof Player p) || p.getWorld() != c.getWorld()) yield "§8—";
                yield "§e" + (int) p.getLocation().distance(c) + " m";
            }
            case "chronons" -> player instanceof Player p ? String.valueOf(chronon.count(p)) : "0";
            default -> null;
        };
    }

    private static String fmt(int s) {
        return String.format("%d:%02d", Math.max(0, s) / 60, Math.max(0, s) % 60);
    }
}
