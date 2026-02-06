from collections import Counter
import heapq

class Solution:
    def topKFrequent(self, nums: List[int], k: int) -> List[int]:
        # Count frequencies
        count = Counter(nums)
        
        # Use min heap to keep top k elements
        heap = []
        for num, freq in count.items():
            heapq.heappush(heap, (freq, num))
            if len(heap) > k:
                heapq.heappop(heap)
        
        return [num for freq, num in heap]
    

# Time Complexity: O(n)O(n)
# O(n)
# Space Complexity: O(n)O(n)
# O(n)
# How it works:

# Count the frequency of each element
# Create buckets where freq[i] contains all elements that appear i times
# Iterate from the highest frequency bucket downward and collect k elements

class Solution:
    def topKFrequent(self, nums: List[int], k: int) -> List[int]:
        # Count frequency of each number
        count = {}
        for num in nums:
            count[num] = count.get(num, 0) + 1
        
        # Create buckets where index = frequency
        freq = [[] for i in range(len(nums) + 1)]
        for num, cnt in count.items():
            freq[cnt].append(num)
        
        # Collect k most frequent elements from highest frequency
        res = []
        for i in range(len(freq) - 1, 0, -1):
            for num in freq[i]:
                res.append(num)
                if len(res) == k:
                    return res
        
        return res