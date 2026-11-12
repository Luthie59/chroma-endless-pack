package fr.citadelle.messages;

import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.World;
import org.bukkit.WorldCreator;
import org.bukkit.block.Biome;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabExecutor;
import org.bukkit.entity.Display;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerChangedWorldEvent;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerMoveEvent;
import org.bukkit.event.player.PlayerTeleportEvent;
import org.bukkit.generator.BiomeProvider;
import org.bukkit.generator.ChunkGenerator;
import org.bukkit.generator.WorldInfo;
import org.bukkit.util.Transformation;
import org.joml.Quaternionf;

import java.util.HexFormat;
import java.util.List;
import java.util.UUID;

/**
 * "L'Instant Éternel": a private void world frozen at sunset, holding the floating island built in tribute to the
 * friendship of Luthie59 & Margot59. Only holders of citadelle.amitie (granted per player) may enter, by /amitie.
 */
final class Amitie implements Listener, TabExecutor {

    static final String WORLD = "amitie";
    private static final String PERM = "citadelle.amitie";
    private static final long SUNSET = 12350L;
    private static final double VOID_RESCUE_Y = 40;
    private static final String P = "§d✿ §7";
    private static final UUID PACK_ID = UUID.nameUUIDFromBytes("citadelle-amitie-pack".getBytes(java.nio.charset.StandardCharsets.UTF_8));
    /** resolvable profiles (SNBT): Margot's chosen skin comes from the Instant Éternel overlay pack. */
    private static final String[] FRIENDS = {"\"Luthie59\"", "{name:\"Margot59\",texture:\"chroma:skins/margot\"}"};
    private static final int RING_STEP = 5;              // every 10 ticks, interpolated
    private static final double CLOCK_SWAY = 12;
    private static final double STATUE_X = 1.5, STATUE_Z0 = 0.0, STATUE_GAP = 1.0, STATUE_Y = 121.35;

    /** empty chunks: the island is placed as a structure. */
    private static final class VoidGenerator extends ChunkGenerator {
        @Override public boolean shouldGenerateNoise() { return false; }
        @Override public boolean shouldGenerateSurface() { return false; }
        @Override public boolean shouldGenerateCaves() { return false; }
        @Override public boolean shouldGenerateDecorations() { return false; }
        @Override public boolean shouldGenerateMobs() { return false; }
        @Override public boolean shouldGenerateStructures() { return false; }
    }

    private static final class CherrySky extends BiomeProvider {
        @Override public Biome getBiome(WorldInfo info, int x, int y, int z) { return Biome.CHERRY_GROVE; }
        @Override public List<Biome> getBiomes(WorldInfo info) { return List.of(Biome.CHERRY_GROVE); }
    }

    private final CitadelleMessages plugin;
    private World world;
    private float clockYaw;
    private int tick;

    Amitie(CitadelleMessages plugin) {
        this.plugin = plugin;
        world = Bukkit.getWorld(WORLD);
        if (world == null) {
            world = new WorldCreator(WORLD).generator(new VoidGenerator()).biomeProvider(new CherrySky())
                    .generateStructures(false).createWorld();
        }
        if (world == null) {
            plugin.getLogger().warning("Monde « " + WORLD + " » impossible à créer.");
            return;
        }
        rule("advance_time", "doDaylightCycle");
        rule("advance_weather", "doWeatherCycle");
        rule("spawn_mobs", "doMobSpawning");
        rule("spawn_monsters", null);
        rule("spawn_phantoms", "doInsomnia");
        rule("spawn_patrols", "doPatrolSpawning");
        rule("spawn_wandering_traders", "doTraderSpawning");
        world.setTime(SUNSET);
        world.setStorm(false);
        world.setThundering(false);
        world.setSpawnLocation(arrival());
        Bukkit.getScheduler().runTaskTimer(plugin, this::ambience, 40L, 2L);
    }

    /** the GameRule API differs between Spigot and Paper builds: use the vanilla command, which never changes shape. */
    private void rule(String name, String legacy) {
        String dim = world.getKey().toString();
        Bukkit.dispatchCommand(Bukkit.getConsoleSender(), "minecraft:execute in " + dim + " run minecraft:gamerule " + name + " false");
    }

    private Location arrival() {
        return new Location(world, plugin.getConfig().getDouble("amitie.arrivee.x", 22.5), plugin.getConfig().getDouble("amitie.arrivee.y", 121),
                plugin.getConfig().getDouble("amitie.arrivee.z", 0.5), (float) plugin.getConfig().getDouble("amitie.arrivee.yaw", 90), 0f);
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (!(sender instanceof Player p)) { sender.sendMessage(P + "Commande en jeu uniquement."); return true; }
        if (!p.hasPermission(PERM) || world == null) { p.sendMessage(P + "Ce lieu n'existe que pour ceux qu'il attend."); return true; }
        if (args.length > 0 && args[0].equalsIgnoreCase("statues")) {
            double y = STATUE_Y;
            try {
                if (args.length > 1) y = Double.parseDouble(args[1]);
            } catch (NumberFormatException e) {
                p.sendMessage(P + "Hauteur invalide.");
                return true;
            }
            placeStatues(y);
            p.sendMessage(P + "Vos statues sont assises sur le banc (hauteur " + y + ").");
            return true;
        }
        if (args.length > 0 && args[0].equalsIgnoreCase("definir")) {
            if (p.getWorld() != world) { p.sendMessage(P + "Place-toi sur l'île pour choisir l'arrivée."); return true; }
            Location l = p.getLocation();
            plugin.getConfig().set("amitie.arrivee.x", l.getX());
            plugin.getConfig().set("amitie.arrivee.y", l.getY());
            plugin.getConfig().set("amitie.arrivee.z", l.getZ());
            plugin.getConfig().set("amitie.arrivee.yaw", (double) l.getYaw());
            plugin.saveConfig();
            world.setSpawnLocation(l);
            p.sendMessage(P + "Point d'arrivée enregistré.");
            return true;
        }
        p.teleport(arrival());
        p.sendTitle("§6§l✿ L'Instant Éternel ✿", "§dLuthie59 §7& §dMargot59", 20, 80, 30);
        p.playSound(p.getLocation(), Sound.BLOCK_AMETHYST_BLOCK_RESONATE, 0.8f, 0.7f);
        return true;
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String alias, String[] args) {
        return sender.hasPermission(PERM) && args.length == 1 ? List.of("definir", "statues") : List.of();
    }

    /**
     * The two friends, sitting side by side on the bench and facing the sunset: player-skinned mannequins
     * (vanilla resolves the skin from the name) riding invisible marker armour stands. Vanilla commands are used
     * on purpose, the Mannequin API differs between Spigot and Paper.
     */
    private void placeStatues(double y) {
        String dim = world.getKey().toString();
        console("minecraft:execute in " + dim + " run minecraft:kill @e[tag=amitie_statue]");
        for (int i = 0; i < FRIENDS.length; i++) {
            double z = STATUE_Z0 + i * STATUE_GAP;
            String rider = "{id:\"minecraft:mannequin\",profile:" + FRIENDS[i] + ",immovable:1b,hide_description:1b,"
                    + "Invulnerable:1b,Silent:1b,PersistenceRequired:1b,Rotation:[90f,0f],Tags:[\"amitie\",\"amitie_statue\"]}";
            console(String.format(java.util.Locale.ROOT, "minecraft:execute in %s run minecraft:summon minecraft:armor_stand %.2f %.2f %.2f "
                    + "{Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,Rotation:[90f,0f],Tags:[\"amitie\",\"amitie_statue\"],"
                    + "Passengers:[%s]}", dim, STATUE_X, y, z, rider));
        }
    }

    private static void spin(Display d, Quaternionf q) {
        Transformation t = d.getTransformation();
        d.setInterpolationDelay(0);
        d.setInterpolationDuration(RING_STEP * 2);
        d.setTransformation(new Transformation(t.getTranslation(), q, t.getScale(), t.getRightRotation()));
    }

    private static void console(String cmd) {
        Bukkit.dispatchCommand(Bukkit.getConsoleSender(), cmd);
    }

    // ------------------------------------------------------------------ overlay pack, only inside this world

    private void sendPack(Player p) {
        String url = plugin.getConfig().getString("amitie.pack.url", "");
        String sha = plugin.getConfig().getString("amitie.pack.sha1", "");
        if (url.isEmpty() || sha.length() != 40) return;
        try {
            p.addResourcePack(PACK_ID, url, HexFormat.of().parseHex(sha), "§dL'Instant Éternel", false);
        } catch (LinkageError | RuntimeException e) {
            plugin.getLogger().warning("Pack de l'Instant Éternel non envoyé : " + e);
        }
    }

    private static void dropPack(Player p) {
        try {
            p.removeResourcePack(PACK_ID);
        } catch (LinkageError | RuntimeException ignored) {
            // older clients / servers: nothing to remove
        }
    }

    @EventHandler
    public void onWorldChange(PlayerChangedWorldEvent event) {
        if (world == null) return;
        Player p = event.getPlayer();
        if (p.getWorld() == world) sendPack(p);
        else if (event.getFrom() == world) dropPack(p);
    }

    @EventHandler
    public void onJoin(PlayerJoinEvent event) {
        if (world != null && event.getPlayer().getWorld() == world) sendPack(event.getPlayer());
    }

    /** nobody else gets in: any teleport into the world without the permission is refused. */
    @EventHandler(priority = EventPriority.HIGHEST, ignoreCancelled = true)
    public void onTeleport(PlayerTeleportEvent event) {
        if (world == null || event.getTo() == null || event.getTo().getWorld() != world) return;
        if (!event.getPlayer().hasPermission(PERM)) {
            event.setCancelled(true);
            event.getPlayer().sendMessage(P + "Ce lieu n'existe que pour ceux qu'il attend.");
        }
    }

    /** falling off the island never kills: back to the arrival point. */
    @EventHandler(ignoreCancelled = true)
    public void onFall(PlayerMoveEvent event) {
        if (world == null || event.getTo() == null || event.getTo().getWorld() != world || event.getTo().getY() > VOID_RESCUE_Y) return;
        Player p = event.getPlayer();
        p.setFallDistance(0f);
        Bukkit.getScheduler().runTask(plugin, () -> p.teleport(arrival()));
    }

    /** falling petals, sparkling stars, and the clock slowly turning on its pedestal. */
    private void ambience() {
        if (world == null || world.getPlayers().isEmpty()) return;
        clockYaw = (clockYaw + 2f) % 360f;
        tick++;
        boolean ringStep = tick % RING_STEP == 0;
        float face = (float) plugin.getConfig().getDouble("amitie.horloge.yaw", -90.0);
        for (Entity e : world.getEntities()) {
            java.util.Set<String> tags = e.getScoreboardTags();
            if (tags.contains("amitie_horloge")) {
                // the Eternal Clock faces the bench and sways gently, as if breathing
                e.setRotation(face + (float) (CLOCK_SWAY * Math.sin(tick * .03)), 0f);
                if (Math.random() < .12) world.spawnParticle(Particle.WAX_ON, e.getLocation(), 1, 1.2, 1.2, 1.2, .02);
            } else if (tags.contains("amitie_etoile")) {
                e.setRotation(-clockYaw, 0f);
                if (Math.random() < .25) world.spawnParticle(Particle.END_ROD, e.getLocation(), 1, .3, .3, .3, .01);
            } else if (ringStep && tags.contains("amitie_anneau_a") && e instanceof Display d) {
                spin(d, new Quaternionf().rotateY(tick * .045f).rotateX(.45f));
            } else if (ringStep && tags.contains("amitie_anneau_b") && e instanceof Display d) {
                spin(d, new Quaternionf().rotateX(tick * .035f).rotateZ(-.6f));
            }
        }
        Location arch = new Location(world, 0.5, 129, 0.5);
        world.spawnParticle(Particle.CHERRY_LEAVES, arch, 2, 4, 2, 7, 0);
        if (Math.random() < .08) world.spawnParticle(Particle.HEART, new Location(world, 1.5, 122.6, 0.5), 1, .4, .2, .6, 0);
    }
}
