class GameStats:
    """Tracks game statistics for a single player"""
    
    def __init__(self, player_id):
        self.player_id = player_id
        self.reset()
    
    def reset(self):
        """Reset all statistics"""
        self.shots_fired = 0
        self.hits = 0
        self.misses = 0
        self.ships_sunk = 0
        self.start_time = None
        self.end_time = None
    
    def record_shot(self, hit, ship_sunk=False):
        """Record a shot's outcome"""
        self.shots_fired += 1
        
        if hit:
            self.hits += 1
            if ship_sunk:
                self.ships_sunk += 1
        else:
            self.misses += 1
    
    def get_accuracy(self):
        """Calculate shot accuracy as a percentage"""
        if self.shots_fired == 0:
            return 0.0
        
        return (self.hits / self.shots_fired) * 100.0
    
    def get_stats_summary(self):
        """Get a dictionary of summary statistics"""
        return {
            "player_id": self.player_id,
            "shots_fired": self.shots_fired,
            "hits": self.hits,
            "misses": self.misses,
            "ships_sunk": self.ships_sunk,
            "accuracy": f"{self.get_accuracy():.1f}%"
        }