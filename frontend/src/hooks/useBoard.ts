import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getBoard } from '@/api/boards';
import {
  createCard as apiCreateCard,
  updateCard as apiUpdateCard,
  deleteCard as apiDeleteCard,
  moveCard as apiMoveCard,
} from '@/api/cards';
import type { BoardColumn, Card, CardType, CardPriority } from '@/types';

export function useBoard(projectId: string | undefined) {
  return useQuery<BoardColumn[]>({
    queryKey: ['board', projectId],
    queryFn: () => getBoard(projectId!),
    enabled: !!projectId,
    refetchOnWindowFocus: true,
  });
}

export function useMoveCard(projectId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      cardId,
      data,
    }: {
      cardId: string;
      data: { column_id: string; position: number };
    }) => apiMoveCard(cardId, data),
    onMutate: async ({ cardId, data }) => {
      await queryClient.cancelQueries({ queryKey: ['board', projectId] });
      const previousBoard = queryClient.getQueryData<BoardColumn[]>(['board', projectId]);

      if (previousBoard) {
        const newBoard = previousBoard.map((col) => ({
          ...col,
          cards: col.cards ? [...col.cards] : [],
        }));

        let movedCard: Card | undefined;
        for (const col of newBoard) {
          const cardIndex = col.cards!.findIndex((c) => c.id === cardId);
          if (cardIndex !== -1) {
            movedCard = col.cards!.splice(cardIndex, 1)[0];
            break;
          }
        }

        if (movedCard) {
          const targetCol = newBoard.find((col) => col.id === data.column_id);
          if (targetCol) {
            movedCard = { ...movedCard, column_id: data.column_id, position: data.position };
            targetCol.cards!.splice(data.position, 0, movedCard);
            targetCol.cards!.forEach((c, i) => {
              c.position = i;
            });
          }
        }

        queryClient.setQueryData(['board', projectId], newBoard);
      }

      return { previousBoard };
    },
    onError: (_err, _vars, context) => {
      if (context?.previousBoard) {
        queryClient.setQueryData(['board', projectId], context.previousBoard);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['board', projectId] });
    },
  });
}

export function useCreateCard(projectId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      title: string;
      description?: string;
      card_type?: CardType;
      column_id?: string;
      parent_id?: string | null;
      priority?: CardPriority;
      start_date?: string | null;
      due_date?: string | null;
    }) => apiCreateCard(projectId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['board', projectId] });
    },
  });
}

export function useUpdateCard(projectId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      cardId,
      data,
    }: {
      cardId: string;
      data: {
        title?: string;
        description?: string;
        priority?: CardPriority;
        start_date?: string | null;
        due_date?: string | null;
        parent_id?: string | null;
      };
    }) => apiUpdateCard(cardId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['board', projectId] });
    },
  });
}

export function useDeleteCard(projectId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (cardId: string) => apiDeleteCard(cardId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['board', projectId] });
    },
  });
}
